from __future__ import annotations

from datetime import date
from io import BytesIO

from django.contrib import messages
from django.db.models import Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView

from core.ticket_pdf import TicketPDF, estimate_height
from usuarios.permissions import RolePermissionRequiredMixin, user_has_perm

from .forms import PagoTrabajadorForm, SueldoHistorialForm, TrabajadorForm
from .models import PagoTrabajador, SueldoHistorial, Trabajador


class TrabajadorListView(RolePermissionRequiredMixin, ListView):
    model = Trabajador
    template_name = "trabajadores/trabajador_list.html"
    context_object_name = "trabajadores"
    paginate_by = 20
    required_perms = ["trabajadores.view"]


class TrabajadorDetailView(RolePermissionRequiredMixin, DetailView):
    model = Trabajador
    template_name = "trabajadores/trabajador_detail.html"
    context_object_name = "trabajador"
    required_perms = ["trabajadores.view"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t: Trabajador = self.object
        total_pagado = t.pagos.aggregate(t=Sum("monto"))["t"] or 0
        ctx["total_pagado"] = total_pagado
        ctx["pagos_recientes"] = t.pagos.select_related("usuario_registro").all()[:6]
        ctx["sueldos_recientes"] = t.sueldos.select_related("usuario_registro").all()[:6]
        return ctx


class TrabajadorCreateView(RolePermissionRequiredMixin, CreateView):
    model = Trabajador
    form_class = TrabajadorForm
    template_name = "trabajadores/trabajador_form.html"
    success_url = reverse_lazy("trabajadores:list")
    required_perms = ["trabajadores.create"]

    def form_valid(self, form):
        messages.success(self.request, "Trabajador registrado correctamente.")
        return super().form_valid(form)


class TrabajadorUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = Trabajador
    form_class = TrabajadorForm
    template_name = "trabajadores/trabajador_form.html"
    success_url = reverse_lazy("trabajadores:list")
    required_perms = ["trabajadores.update"]

    def form_valid(self, form):
        messages.success(self.request, "Trabajador actualizado correctamente.")
        return super().form_valid(form)


class TrabajadorDeleteView(RolePermissionRequiredMixin, DeleteView):
    model = Trabajador
    template_name = "trabajadores/trabajador_confirm_delete.html"
    success_url = reverse_lazy("trabajadores:list")
    required_perms = ["trabajadores.delete"]

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Trabajador eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


class PagoTrabajadorListView(RolePermissionRequiredMixin, ListView):
    model = PagoTrabajador
    template_name = "trabajadores/pago_list.html"
    context_object_name = "pagos"
    paginate_by = 20
    required_perms = ["trabajadores.pagos.view"]

    def get_queryset(self):
        self.trabajador = get_object_or_404(Trabajador, pk=self.kwargs["trabajador_id"])
        return PagoTrabajador.objects.filter(trabajador=self.trabajador).select_related("usuario_registro")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajador"] = self.trabajador
        ctx["total_pagado"] = self.get_queryset().aggregate(t=Sum("monto"))["t"] or 0
        return ctx


class PagoTrabajadorCreateView(RolePermissionRequiredMixin, CreateView):
    model = PagoTrabajador
    form_class = PagoTrabajadorForm
    template_name = "trabajadores/pago_form.html"
    required_perms = ["trabajadores.pagos.create"]

    def dispatch(self, request, *args, **kwargs):
        self.trabajador = get_object_or_404(Trabajador, pk=self.kwargs["trabajador_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["fecha_pago"] = timezone.localdate()
        return initial

    def form_valid(self, form):
        form.instance.trabajador = self.trabajador
        form.instance.usuario_registro = self.request.user
        if not (form.cleaned_data.get("numero_comprobante") or "").strip():
            ultimo = PagoTrabajador.objects.order_by("-id").first()
            n = (ultimo.id + 1) if ultimo else 1
            form.instance.numero_comprobante = f"TRB-{n:06d}"
        messages.success(self.request, "Pago registrado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("trabajadores:pago_comprobante", args=[self.trabajador.pk, self.object.pk])


class PagoTrabajadorUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = PagoTrabajador
    form_class = PagoTrabajadorForm
    template_name = "trabajadores/pago_form.html"
    context_object_name = "pago"
    required_perms = ["trabajadores.pagos.update"]

    def dispatch(self, request, *args, **kwargs):
        self.trabajador = get_object_or_404(Trabajador, pk=kwargs["trabajador_id"])
        self.object = get_object_or_404(
            PagoTrabajador, pk=kwargs["pk"], trabajador=self.trabajador
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajador"] = self.trabajador
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Pago actualizado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("trabajadores:pago_list", args=[self.trabajador.pk])


class PagoTrabajadorComprobanteView(RolePermissionRequiredMixin, DetailView):
    """Vista de comprobante/ticket para imprimir."""
    model = PagoTrabajador
    template_name = "trabajadores/pago_comprobante.html"
    context_object_name = "pago"
    required_perms = ["trabajadores.pagos.ticket"]

    def get_queryset(self):
        return PagoTrabajador.objects.filter(
            trabajador_id=self.kwargs["trabajador_id"]
        ).select_related("trabajador", "usuario_registro")


def pago_trabajador_comprobante_pdf(request, trabajador_id: int, pk: int):
    if not request.user.is_authenticated:
        raise Http404()
    if not user_has_perm(request.user, "trabajadores.pagos.pdf"):
        raise Http404()

    pago = get_object_or_404(
        PagoTrabajador.objects.select_related("trabajador", "usuario_registro"),
        pk=pk,
        trabajador_id=trabajador_id,
    )

    base_lines = 18
    extra_lines = 0
    if pago.observaciones:
        extra_lines += min(3, (len(pago.observaciones) // 30) + 1)
    height_pt = estimate_height(base_lines + extra_lines)

    pdf = TicketPDF(height_pt=height_pt)
    buffer = BytesIO()
    pdf.build_canvas(buffer)

    pdf.text_center("LATINFORCE", bold=True)
    pdf.text_center("PAGO A TRABAJADOR", bold=True)
    pdf.text_center(str(pago.numero_comprobante or "—"), bold=True, size=11)
    pdf.dashed_hr()

    pdf.kv("FECHA", pago.fecha_pago.strftime("%d/%m/%Y"))
    pdf.kv("TRABAJADOR", (pago.trabajador.nombre_completo or "—")[:40])
    pdf.kv("DOCUMENTO", pago.trabajador.documento or "—")
    pdf.kv("CONCEPTO", str(pago.concepto)[:24])
    pdf.kv("MÉTODO", str(pago.get_metodo_pago_display()))
    pdf.dashed_hr()

    pdf.c.setFont(pdf.style.font_bold, 11)
    pdf.c.drawString(pdf.style.margin_pt, pdf.y, "TOTAL")
    pdf.c.drawRightString(pdf.width - pdf.style.margin_pt, pdf.y, f"S/ {pago.monto:.2f}")
    pdf.newline(1.2)

    if pago.usuario_registro:
        pdf.text_left(
            f"USUARIO  {pago.usuario_registro.username}".upper(),
            size=pdf.style.size_small,
        )
    pdf.text_left(
        timezone.now().strftime("%d/%m/%Y %I:%M %p"),
        size=pdf.style.size_small,
    )

    pdf.c.showPage()
    pdf.c.save()
    buffer.seek(0)

    filename = f"{pago.numero_comprobante or f'pago_trb_{pago.pk}'}_80mm.pdf"
    return FileResponse(
        buffer, as_attachment=True, filename=filename, content_type="application/pdf"
    )


class SueldoHistorialListView(RolePermissionRequiredMixin, ListView):
    model = SueldoHistorial
    template_name = "trabajadores/sueldo_list.html"
    context_object_name = "sueldos"
    paginate_by = 30
    required_perms = ["trabajadores.sueldos.view"]

    def get_queryset(self):
        self.trabajador = get_object_or_404(Trabajador, pk=self.kwargs["trabajador_id"])
        return SueldoHistorial.objects.filter(trabajador=self.trabajador).select_related("usuario_registro")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajador"] = self.trabajador
        return ctx


class SueldoHistorialCreateView(RolePermissionRequiredMixin, CreateView):
    model = SueldoHistorial
    form_class = SueldoHistorialForm
    template_name = "trabajadores/sueldo_form.html"
    required_perms = ["trabajadores.sueldos.create"]

    def dispatch(self, request, *args, **kwargs):
        self.trabajador = get_object_or_404(Trabajador, pk=self.kwargs["trabajador_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["fecha_inicio"] = timezone.localdate()
        initial["sueldo_mensual"] = self.trabajador.sueldo_mensual
        return initial

    def form_valid(self, form):
        form.instance.trabajador = self.trabajador
        form.instance.usuario_registro = self.request.user
        # sincroniza el sueldo actual del trabajador
        self.trabajador.sueldo_mensual = form.cleaned_data["sueldo_mensual"]
        self.trabajador.save(update_fields=["sueldo_mensual"])
        messages.success(self.request, "Sueldo actualizado y registrado en historial.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("trabajadores:sueldo_list", args=[self.trabajador.pk])


class ReportePagosTrabajadoresView(RolePermissionRequiredMixin, TemplateView):
    template_name = "trabajadores/reporte_pagos.html"
    required_perms = ["trabajadores.reportes.view"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        year = int(self.request.GET.get("year") or hoy.year)
        month = int(self.request.GET.get("month") or hoy.month)
        trabajador_id = (self.request.GET.get("trabajador") or "").strip()

        # rango mensual
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)

        pagos = PagoTrabajador.objects.select_related("trabajador", "usuario_registro").filter(
            fecha_pago__gte=start, fecha_pago__lt=end
        )
        if trabajador_id:
            pagos = pagos.filter(trabajador_id=trabajador_id)

        ctx["pagos"] = pagos.order_by("-fecha_pago", "-id")
        ctx["total_mes"] = pagos.aggregate(t=Sum("monto"))["t"] or 0
        ctx["trabajadores"] = Trabajador.objects.all()
        ctx["f_year"] = year
        ctx["f_month"] = month
        ctx["f_trabajador"] = trabajador_id
        return ctx

