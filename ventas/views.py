import json
from io import BytesIO
from decimal import Decimal

from django.contrib import messages
from usuarios.permissions import RolePermissionRequiredMixin, user_has_perm
from django.http import FileResponse, Http404
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.timezone import now
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from inventario.models import Producto
from core.ticket_pdf import TicketPDF, estimate_height, mm_to_pt
from core.numero_a_letras import monto_soles_en_letras
from .forms import VentaForm
from .models import Venta, VentaDetalle


class VentaListView(RolePermissionRequiredMixin, ListView):
    model = Venta
    template_name = 'ventas/venta_list.html'
    context_object_name = 'ventas'
    paginate_by = 20
    required_perms = ["ventas.view"]

    def get_queryset(self):
        qs = (
            Venta.objects.select_related('cliente', 'usuario')
            .prefetch_related('detalles')
            .order_by('-fecha_emision', '-id')
        )
        q = (self.request.GET.get('q') or '').strip()
        tipo = (self.request.GET.get('tipo') or '').strip()
        desde = (self.request.GET.get('desde') or '').strip()
        hasta = (self.request.GET.get('hasta') or '').strip()

        if q:
            qs = qs.filter(
                Q(serie__icontains=q)
                | Q(numero_comprobante__icontains=q)
                | Q(cliente__nombres__icontains=q)
                | Q(cliente__apellidos__icontains=q)
                | Q(cliente__dni__icontains=q)
            )
        if tipo:
            qs = qs.filter(tipo_comprobante=tipo)
        if desde:
            qs = qs.filter(fecha_emision__gte=desde)
        if hasta:
            qs = qs.filter(fecha_emision__lte=hasta)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = (self.request.GET.get('q') or '').strip()
        tipo = (self.request.GET.get('tipo') or '').strip()
        desde = (self.request.GET.get('desde') or '').strip()
        hasta = (self.request.GET.get('hasta') or '').strip()

        hoy = timezone.localdate()
        inicio_mes = hoy.replace(day=1)

        base = Venta.objects.filter(estado='emitido')
        ctx['kpi_hoy_total'] = base.filter(fecha_emision=hoy).aggregate(t=Sum('total'))['t'] or Decimal('0')
        ctx['kpi_mes_total'] = base.filter(fecha_emision__gte=inicio_mes, fecha_emision__lte=hoy).aggregate(t=Sum('total'))['t'] or Decimal('0')
        ctx['kpi_total_count'] = base.aggregate(c=Count('id'))['c'] or 0

        ctx['f_q'] = q
        ctx['f_tipo'] = tipo
        ctx['f_desde'] = desde
        ctx['f_hasta'] = hasta
        ctx['tipos'] = Venta.TIPO_COMPROBANTE
        return ctx


class VentaCreateView(RolePermissionRequiredMixin, CreateView):
    model = Venta
    form_class = VentaForm
    template_name = 'ventas/venta_form.html'
    success_url = reverse_lazy('ventas:list')
    required_perms = ["ventas.create"]

    def get_initial(self):
        initial = super().get_initial()
        initial['fecha_emision'] = timezone.now().date()
        initial['serie'] = 'BB01'
        return initial

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        form.instance.estado = 'emitido'
        # Número de comprobante
        ultimo = Venta.objects.filter(serie=form.instance.serie).order_by('-id').first()
        n = (ultimo.id + 1) if ultimo else 1
        form.instance.numero_comprobante = f"{n:06d}"
        self.object = form.save()

        # Detalles desde JSON
        items_json = self.request.POST.get('items_json', '[]')
        try:
            items = json.loads(items_json)
        except json.JSONDecodeError:
            items = []

        for it in items:
            producto_id = it.get('producto_id')
            cantidad = Decimal(str(it.get('cantidad', 0)))
            precio = Decimal(str(it.get('precio', 0)))
            if not producto_id or cantidad <= 0:
                continue
            producto = get_object_or_404(Producto, pk=producto_id, activo=True)
            permitir_sin_stock = bool(producto.permitir_vender_sin_stock)
            if producto.stock < int(cantidad) and not permitir_sin_stock:
                messages.warning(
                    self.request,
                    f'Stock insuficiente de "{producto.nombre}". Hay {producto.stock} {producto.unidad}.'
                )
                continue
            VentaDetalle.objects.create(
                venta=self.object,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio,
            )
            # Descontar stock
            if permitir_sin_stock:
                producto.stock = max(0, producto.stock - int(cantidad))
            else:
                producto.stock -= int(cantidad)
            producto.save(update_fields=['stock'])
        messages.success(self.request, 'Venta procesada correctamente.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('ventas:comprobante', args=[self.object.pk])


class VentaComprobanteView(RolePermissionRequiredMixin, DetailView):
    model = Venta
    template_name = 'ventas/venta_comprobante.html'
    context_object_name = 'venta'
    required_perms = ["ventas.ticket"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        venta: Venta = ctx["venta"]
        total = Decimal(str(venta.total or 0))
        ctx["total_letras"] = monto_soles_en_letras(total)
        if venta.tipo_comprobante == "factura" and total > 0:
            igv = (total * Decimal("0.18") / Decimal("1.18"))
            gravado = total - igv
        else:
            igv = Decimal("0")
            gravado = total
        ctx["igv_calc"] = igv.quantize(Decimal("0.01"))
        ctx["gravado_calc"] = gravado.quantize(Decimal("0.01"))
        ctx["moneda"] = "SOLES"
        ctx["now"] = now()
        return ctx


class VentaDetailView(RolePermissionRequiredMixin, DetailView):
    model = Venta
    template_name = 'ventas/venta_detail.html'
    context_object_name = 'venta'
    required_perms = ["ventas.view"]


def venta_comprobante_pdf(request, pk: int):
    if not request.user.is_authenticated:
        raise Http404()
    if not user_has_perm(request.user, "ventas.pdf"):
        raise Http404()

    venta = get_object_or_404(
        Venta.objects.select_related('cliente', 'usuario').prefetch_related('detalles__producto'),
        pk=pk,
    )
    detalles = list(venta.detalles.all())

    # Estimación de alto dinámico (en points) para ticket 80mm
    # Consideramos que cada item puede ocupar 1-2 líneas según el nombre.
    base_lines = 18  # cabecera + datos + totales + pie
    item_lines = 0
    for d in detalles:
        nombre = getattr(d.producto, "nombre", "") or ""
        # aproximación simple: 28 caracteres por línea aprox en 80mm con 8-9pt
        item_lines += max(1, (len(nombre) // 28) + (1 if (len(nombre) % 28) else 0))
    total_lines = base_lines + item_lines + (2 if venta.tipo_comprobante in ("factura", "boleta") else 0)
    height_pt = estimate_height(total_lines, extra_pt=mm_to_pt(20))

    pdf = TicketPDF(height_pt=height_pt)
    buffer = BytesIO()
    pdf.build_canvas(buffer)

    # Cabecera similar a comprobante
    titulo = venta.get_tipo_comprobante_display().upper() if hasattr(venta, "get_tipo_comprobante_display") else "COMPROBANTE"
    pdf.text_center(titulo, bold=True)
    pdf.text_center(f"{venta.serie}-{venta.numero_comprobante}", bold=True, size=11)
    pdf.dashed_hr()

    cliente = venta.cliente
    dni = getattr(cliente, "dni", "") if cliente else ""
    nombre = getattr(cliente, "nombre_completo", "—") if cliente else "—"
    direccion = (getattr(cliente, "direccion", "") or "").strip() if cliente else ""

    pdf.kv("DOCUMENTO", dni or "—")
    pdf.kv("CLIENTE", (nombre or "—")[:40])
    if direccion:
        # Dirección puede ser larga: 2-3 líneas
        pdf.c.setFont(pdf.style.font_bold, pdf.style.size_small)
        pdf.c.drawString(pdf.style.margin_pt, pdf.y, "DIRECCIÓN")
        pdf.newline(1.0)
        pdf.c.setFont(pdf.style.font, pdf.style.size_small)
        max_w = pdf.width - (2 * pdf.style.margin_pt)
        for ln in pdf.wrap_text(direccion, max_w, pdf.style.font, pdf.style.size_small)[:3]:
            pdf.c.drawString(pdf.style.margin_pt, pdf.y, ln)
            pdf.newline(1.0)

    pdf.kv("F. EMISIÓN", venta.fecha_emision.strftime("%d/%m/%Y"))
    pdf.kv("MONEDA", "SOLES")
    if venta.condicion_pago:
        pdf.kv("COND. PAGO", str(venta.condicion_pago)[:20])
    pdf.dashed_hr()

    # Tabla
    left_x = pdf.style.margin_pt
    right_x = pdf.width - pdf.style.margin_pt
    col_pu = right_x - mm_to_pt(18)
    col_total = right_x
    col_desc_w = col_pu - left_x - mm_to_pt(2)

    pdf.c.setFont(pdf.style.font_bold, pdf.style.size_small)
    pdf.c.drawString(left_x, pdf.y, "DESCRIPCIÓN")
    pdf.c.drawRightString(col_pu, pdf.y, "P/U")
    pdf.c.drawRightString(col_total, pdf.y, "TOTAL")
    pdf.newline(0.9)
    pdf.dashed_hr()

    for d in detalles:
        desc = getattr(d.producto, "nombre", "—") or "—"
        pu = pdf.money(d.precio_unitario)
        tot = pdf.money(d.subtotal)

        # Descripción en 1-2 líneas
        pdf.c.setFont(pdf.style.font, pdf.style.size_small)
        lines = pdf.wrap_text(desc, col_desc_w, pdf.style.font, pdf.style.size_small)
        first = True
        for ln in lines[:2]:
            pdf.c.drawString(left_x, pdf.y, ln)
            if first:
                pdf.c.drawRightString(col_pu, pdf.y, pu.replace("S/ ", ""))
                pdf.c.drawRightString(col_total, pdf.y, tot.replace("S/ ", ""))
                first = False
            pdf.newline(0.95)

    pdf.dashed_hr()

    # Totales (si no tienes IGV guardado, lo calculamos solo para mostrar estilo)
    total = Decimal(str(venta.total or 0))
    if venta.tipo_comprobante == "factura":
        igv = (total * Decimal("0.18") / Decimal("1.18")) if total > 0 else Decimal("0")
        gravado = total - igv
        pdf.kv("GRAVADO", f"S/ {gravado:.2f}")
        pdf.kv("I.G.V. 18%", f"S/ {igv:.2f}")

    pdf.c.setFont(pdf.style.font_bold, 11)
    pdf.c.drawString(left_x, pdf.y, "TOTAL")
    pdf.c.drawRightString(right_x, pdf.y, f"S/ {total:.2f}")
    pdf.newline(1.2)

    pdf.c.setFont(pdf.style.font_bold, pdf.style.size_small)
    max_w = pdf.width - (2 * pdf.style.margin_pt)
    for ln in pdf.wrap_text(monto_soles_en_letras(total), max_w, pdf.style.font_bold, pdf.style.size_small)[:2]:
        pdf.c.drawString(left_x, pdf.y, ln)
        pdf.newline(1.0)

    # Pie
    usuario = getattr(venta.usuario, "username", "") if venta.usuario else ""
    if usuario:
        pdf.c.setFont(pdf.style.font, pdf.style.size_small)
        pdf.c.drawString(left_x, pdf.y, f"USUARIO  {usuario}".upper())
        pdf.newline(1.0)
    pdf.c.setFont(pdf.style.font, pdf.style.size_small)
    pdf.c.drawString(left_x, pdf.y, timezone.now().strftime("%d/%m/%Y %I:%M %p"))
    pdf.newline(1.0)

    pdf.c.showPage()
    pdf.c.save()
    buffer.seek(0)

    filename = f"{venta.serie}-{venta.numero_comprobante}_80mm.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type="application/pdf")
