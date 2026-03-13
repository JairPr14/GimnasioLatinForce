"""
Vistas del módulo Pagos.
"""
from datetime import timedelta
from io import BytesIO

from django.contrib import messages
from usuarios.permissions import RolePermissionRequiredMixin
from django.db.models import Sum
from django.http import FileResponse, Http404
from usuarios.permissions import user_has_perm
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView

from clientes.models import Cliente
from planes.models import Plan
from ventas.models import Venta
from core.ticket_pdf import TicketPDF, estimate_height
from .forms import PagoForm, DeudaForm
from .models import Pago, Deuda


class PagoListView(RolePermissionRequiredMixin, ListView):
    """Listado de pagos con filtros."""
    model = Pago
    template_name = 'pagos/pago_list.html'
    context_object_name = 'pagos'
    paginate_by = 20
    required_perms = ["pagos.view"]

    def get_queryset(self):
        qs = Pago.objects.select_related('cliente', 'plan', 'deuda', 'usuario_registro')
        cliente_id = self.request.GET.get('cliente')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        metodo = self.request.GET.get('metodo')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        if fecha_desde:
            qs = qs.filter(fecha_pago__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_pago__lte=fecha_hasta)
        if metodo:
            qs = qs.filter(metodo_pago=metodo)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clientes'] = Cliente.objects.filter(estado__in=('activo', 'suspendido')).order_by('apellidos')
        return ctx


class PagoCreateView(RolePermissionRequiredMixin, CreateView):
    model = Pago
    form_class = PagoForm
    template_name = 'pagos/pago_form.html'
    success_url = reverse_lazy('pagos:list')
    required_perms = ["pagos.create"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        import json
        planes = Plan.objects.filter(activo=True)
        ctx['planes_precios_json'] = json.dumps({str(p.id): str(p.precio) for p in planes})
        ctx['planes_nombres_json'] = json.dumps({str(p.id): p.nombre for p in planes})
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        # Fecha de emisión = momento actual (al accionar Renovar o abrir nuevo pago).
        initial['fecha_pago'] = timezone.localdate()
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            initial['cliente'] = get_object_or_404(Cliente, pk=cliente_id)
        plan_id = self.request.GET.get('plan')
        if plan_id:
            plan = get_object_or_404(Plan, pk=plan_id, activo=True)
            initial['plan'] = plan
            initial['monto'] = plan.precio
            initial['concepto'] = plan.nombre
        return initial

    def form_valid(self, form):
        form.instance.usuario_registro = self.request.user
        # Generar número de comprobante si está vacío
        if not form.cleaned_data.get('numero_comprobante'):
            ultimo = Pago.objects.order_by('-id').first()
            n = (ultimo.id + 1) if ultimo else 1
            form.instance.numero_comprobante = f"PAG-{n:06d}"
        messages.success(self.request, 'Pago registrado correctamente.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('pagos:comprobante', args=[self.object.pk])


class PagoUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = Pago
    form_class = PagoForm
    template_name = 'pagos/pago_form.html'
    context_object_name = 'pago'
    success_url = reverse_lazy('pagos:list')
    required_perms = ["pagos.update"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        import json
        from planes.models import Plan
        planes = Plan.objects.filter(activo=True)
        ctx['planes_precios_json'] = json.dumps({str(p.id): str(p.precio) for p in planes})
        ctx['planes_nombres_json'] = json.dumps({str(p.id): p.nombre for p in planes})
        return ctx

    def form_valid(self, form):
        messages.success(self.request, 'Pago actualizado correctamente.')
        return super().form_valid(form)


class PagoComprobanteView(RolePermissionRequiredMixin, DetailView):
    """Vista de comprobante/ticket para imprimir."""
    model = Pago
    template_name = 'pagos/pago_comprobante.html'
    context_object_name = 'pago'
    required_perms = ["pagos.ticket"]


def pago_comprobante_pdf(request, pk: int):
    if not request.user.is_authenticated:
        raise Http404()
    if not user_has_perm(request.user, "pagos.pdf"):
        raise Http404()

    pago = get_object_or_404(Pago.objects.select_related('cliente', 'plan', 'usuario_registro'), pk=pk)

    # Alto aproximado (ticket corto)
    base_lines = 18
    extra_lines = 0
    if pago.observaciones:
        extra_lines += min(3, (len(pago.observaciones) // 30) + 1)
    height_pt = estimate_height(base_lines + extra_lines)

    pdf = TicketPDF(height_pt=height_pt)
    buffer = BytesIO()
    pdf.build_canvas(buffer)

    pdf.text_center("LATINFORCE", bold=True)
    pdf.text_center("COMPROBANTE DE PAGO", bold=True)
    pdf.text_center(str(pago.numero_comprobante or "—"), bold=True, size=11)
    pdf.dashed_hr()

    pdf.kv("FECHA", pago.fecha_pago.strftime("%d/%m/%Y"))
    pdf.kv("CLIENTE", (pago.cliente.nombre_completo or "—")[:40])
    pdf.kv("DOCUMENTO", getattr(pago.cliente, "dni", "") or "—")
    if pago.plan:
        pdf.kv("PLAN", str(pago.plan.nombre)[:24])
    pdf.kv("CONCEPTO", str(pago.concepto)[:24])
    pdf.kv("MÉTODO", str(pago.get_metodo_pago_display()))
    pdf.dashed_hr()

    pdf.c.setFont(pdf.style.font_bold, 11)
    pdf.c.drawString(pdf.style.margin_pt, pdf.y, "TOTAL")
    pdf.c.drawRightString(pdf.width - pdf.style.margin_pt, pdf.y, f"S/ {pago.monto:.2f}")
    pdf.newline(1.2)

    if pago.usuario_registro:
        pdf.text_left(f"USUARIO  {pago.usuario_registro.username}".upper(), size=pdf.style.size_small)
    pdf.text_left(timezone.now().strftime("%d/%m/%Y %I:%M %p"), size=pdf.style.size_small)

    pdf.c.showPage()
    pdf.c.save()
    buffer.seek(0)

    filename = f"{pago.numero_comprobante or f'pago_{pago.pk}'}_80mm.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type="application/pdf")


class PagoHistorialClienteView(RolePermissionRequiredMixin, ListView):
    """Historial de pagos de un cliente."""
    model = Pago
    template_name = 'pagos/pago_historial.html'
    context_object_name = 'pagos'
    required_perms = ["pagos.view"]

    def get_queryset(self):
        self.cliente = get_object_or_404(Cliente, pk=self.kwargs['cliente_id'])
        return Pago.objects.filter(cliente=self.cliente).select_related('plan', 'usuario_registro').order_by('-fecha_pago')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cliente'] = self.cliente
        ctx['total_pagado'] = self.get_queryset().aggregate(t=Sum('monto'))['t'] or 0
        return ctx


# ---------- Deudas ----------
class DeudaListView(RolePermissionRequiredMixin, ListView):
    """Deudas pendientes."""
    model = Deuda
    template_name = 'pagos/deuda_list.html'
    context_object_name = 'deudas'
    required_perms = ["deudas.view"]

    def get_queryset(self):
        qs = Deuda.objects.select_related('cliente').order_by('-fecha_creacion')
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clientes'] = Cliente.objects.filter(estado__in=('activo', 'suspendido')).order_by('apellidos')
        deudas = ctx['deudas']
        total_pendiente = 0
        for d in deudas:
            pend = d.monto_pendiente
            if pend > 0:
                total_pendiente += pend
        ctx['total_pendiente'] = total_pendiente
        return ctx


class DeudaCreateView(RolePermissionRequiredMixin, CreateView):
    model = Deuda
    form_class = DeudaForm
    template_name = 'pagos/deuda_form.html'
    success_url = reverse_lazy('pagos:deuda_list')
    required_perms = ["deudas.create"]

    def get_initial(self):
        initial = super().get_initial()
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            initial['cliente'] = get_object_or_404(Cliente, pk=cliente_id)
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Deuda registrada correctamente.')
        return super().form_valid(form)


# ---------- Reportes ----------
class ReporteIngresosView(RolePermissionRequiredMixin, TemplateView):
    """Reportes de ingresos diarios, semanales y mensuales."""
    template_name = 'pagos/reporte_ingresos.html'
    required_perms = ["reportes.view"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        periodo = self.request.GET.get('periodo', 'diario')
        fecha = self.request.GET.get('fecha', hoy.isoformat())
        try:
            fecha_ref = timezone.datetime.strptime(fecha, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            fecha_ref = hoy

        if periodo == 'diario':
            pagos = Pago.objects.filter(fecha_pago=fecha_ref)
            ventas = Venta.objects.filter(fecha_emision=fecha_ref)
        elif periodo == 'semanal':
            inicio = fecha_ref - timedelta(days=fecha_ref.weekday())
            fin = inicio + timedelta(days=6)
            pagos = Pago.objects.filter(fecha_pago__gte=inicio, fecha_pago__lte=fin)
            ventas = Venta.objects.filter(fecha_emision__gte=inicio, fecha_emision__lte=fin)
        else:  # mensual
            inicio = fecha_ref.replace(day=1)
            from calendar import monthrange
            ultimo = monthrange(fecha_ref.year, fecha_ref.month)[1]
            fin = fecha_ref.replace(day=ultimo)
            pagos = Pago.objects.filter(fecha_pago__gte=inicio, fecha_pago__lte=fin)
            ventas = Venta.objects.filter(fecha_emision__gte=inicio, fecha_emision__lte=fin)

        total_pagos = pagos.aggregate(t=Sum('monto'))['t'] or 0
        total_ventas = ventas.aggregate(t=Sum('total'))['t'] or 0
        total_general = (total_pagos or 0) + (total_ventas or 0)
        ctx['pagos'] = pagos.select_related('cliente', 'plan', 'usuario_registro').order_by('-fecha_pago')
        ctx['ventas'] = ventas.select_related('cliente', 'usuario').order_by('-fecha_emision', '-id')
        ctx['total_pagos'] = total_pagos
        ctx['total_ventas'] = total_ventas
        ctx['total_general'] = total_general
        ctx['periodo'] = periodo
        ctx['fecha_ref'] = fecha_ref
        return ctx
