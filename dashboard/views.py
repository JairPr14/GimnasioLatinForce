"""
Vistas del dashboard.
"""
from datetime import date, timedelta

from django.db.models import Sum, Count
from django.utils import timezone
from django.views.generic import TemplateView

from usuarios.permissions import RolePermissionRequiredMixin

from clientes.models import Cliente
from planes.models import Plan
from pagos.models import Pago, Deuda
from ventas.models import Venta


class DashboardView(RolePermissionRequiredMixin, TemplateView):
    """Dashboard principal, accesible solo con login."""
    template_name = 'dashboard/index.html'
    required_perms = ["dashboard.view"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoy = timezone.now().date()
        limite = hoy + timedelta(days=15)
        inicio_mes = hoy.replace(day=1)

        ctx['total_clientes_activos'] = Cliente.objects.filter(estado='activo').count()
        ctx['total_planes_activos'] = Plan.objects.filter(activo=True).count()
        ctx['pagos_hoy'] = Pago.objects.filter(fecha_pago=hoy).count()
        ctx['total_ingresos_hoy'] = Pago.objects.filter(fecha_pago=hoy).aggregate(t=Sum('monto'))['t'] or 0
        ctx['total_ingresos_mes'] = Pago.objects.filter(fecha_pago__gte=inicio_mes, fecha_pago__lte=hoy).aggregate(t=Sum('monto'))['t'] or 0

        # Ventas (emitidas, excluye anuladas)
        ventas_emitidas = Venta.objects.filter(estado='emitido')
        ctx['ventas_hoy'] = ventas_emitidas.filter(fecha_emision=hoy).count()
        ctx['total_ventas_hoy'] = ventas_emitidas.filter(fecha_emision=hoy).aggregate(t=Sum('total'))['t'] or 0
        ctx['total_ventas_mes'] = ventas_emitidas.filter(fecha_emision__gte=inicio_mes, fecha_emision__lte=hoy).aggregate(t=Sum('total'))['t'] or 0
        ctx['total_ventas_count'] = ventas_emitidas.aggregate(c=Count('id'))['c'] or 0

        # Actividad reciente
        ctx['ultimos_pagos'] = (
            Pago.objects.select_related('cliente', 'plan', 'usuario_registro')
            .order_by('-fecha_pago', '-id')[:7]
        )
        ctx['ultimas_ventas'] = (
            Venta.objects.select_related('cliente', 'usuario')
            .order_by('-fecha_emision', '-id')[:7]
        )

        # Deudas pendientes
        from django.db.models import F, Value, DecimalField
        from django.db.models.functions import Coalesce
        deudas = Deuda.objects.annotate(
            abonado=Coalesce(Sum('pago__monto'), Value(0, output_field=DecimalField()))
        ).filter(monto__gt=F('abonado'))
        total_deuda = sum(float(d.monto) - float(d.abonado) for d in deudas)
        ctx['total_deudas_pendientes'] = total_deuda
        ctx['cantidad_deudas'] = deudas.count()

        # Próximos a vencer (clientes con plan que vence en 15 días)
        pagos_con_plan = Pago.objects.filter(plan__isnull=False).select_related('cliente', 'plan').order_by('cliente', '-fecha_pago')
        vencen_pronto = []
        vistos = set()
        for p in pagos_con_plan:
            if p.cliente_id in vistos:
                continue
            vistos.add(p.cliente_id)
            fin = p.fecha_pago + timedelta(days=p.plan.duracion_dias)
            if fin >= hoy and fin <= limite:
                tel = ''.join(c for c in (p.cliente.telefono or '') if c.isdigit())
                if tel.startswith('0'):
                    tel = tel[1:]
                if tel and not tel.startswith('51'):
                    tel = '51' + tel
                msg = f"Hola {p.cliente.nombres}, tu plan {p.plan.nombre} vence el {fin.strftime('%d/%m/%Y')}. Te esperamos para renovar. - LatinForce"
                from urllib.parse import quote
                wa_url = f"https://wa.me/{tel}?text={quote(msg)}" if tel else None
                vencen_pronto.append({'cliente': p.cliente, 'fecha': fin, 'plan': p.plan, 'whatsapp_url': wa_url})
        ctx['proximos_vencer'] = vencen_pronto[:5]

        # Próximos a cumplir años (en los próximos 30 días)
        dias_ventana = 30
        limite_cumple = hoy + timedelta(days=dias_ventana)
        clientes_con_nacimiento = Cliente.objects.filter(
            fecha_nacimiento__isnull=False,
            estado__in=('activo', 'suspendido')
        ).order_by('apellidos', 'nombres')
        proximos_cumple = []
        for c in clientes_con_nacimiento:
            fn = c.fecha_nacimiento
            try:
                next_cumple = date(hoy.year, fn.month, fn.day)
            except ValueError:
                # 29 feb en año no bisiesto
                next_cumple = date(hoy.year, 2, 28)
            if next_cumple < hoy:
                try:
                    next_cumple = date(hoy.year + 1, fn.month, fn.day)
                except ValueError:
                    next_cumple = date(hoy.year + 1, 2, 28)
            if hoy <= next_cumple <= limite_cumple:
                proximos_cumple.append({'cliente': c, 'fecha_cumple': next_cumple})
        proximos_cumple.sort(key=lambda x: x['fecha_cumple'])
        ctx['proximos_cumple_anos'] = proximos_cumple[:10]

        return ctx
