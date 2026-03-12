from __future__ import annotations

from datetime import date
from io import BytesIO

from django.contrib import messages
from django.db.models import Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView

from core.ticket_pdf import TicketPDF, estimate_height
from usuarios.permissions import RolePermissionRequiredMixin, user_has_perm

from .forms import (
    AdelantoTrabajadorForm,
    AsistenciaTrabajadorForm,
    DescuentoTrabajadorForm,
    PagoTrabajadorCreateForm,
    PagoTrabajadorForm,
    SueldoHistorialForm,
    TrabajadorForm,
)
from .models import (
    AdelantoTrabajador,
    AsistenciaTrabajador,
    DescuentoTrabajador,
    PagoTrabajador,
    SueldoHistorial,
    Trabajador,
)


MESES_NOMBRES = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
)


def _meses_pendientes_opciones(trabajador: Trabajador, incluir_mes_edicion: tuple[int, int] | None = None):
    """Opciones para select: solo meses con periodos PENDIENTES (faltantes por pagar)."""
    hoy = timezone.localdate()
    fi = trabajador.fecha_ingreso or hoy
    y_ingreso, m_ingreso = fi.year, fi.month
    opciones = []
    vistos = set()
    qp = _quincenas_pendientes(trabajador)
    for q in qp:
        y, m = q["year"], q["month"]
        if q.get("pendientes"):  # Solo meses con quincenas pendientes
            key = (y, m)
            if key not in vistos:
                vistos.add(key)
                opciones.append((f"{y}-{m:02d}", f"{MESES_NOMBRES[m - 1]} {y}"))
    if not opciones:
        for y in range(y_ingreso, hoy.year + 2):
            m_start = m_ingreso if y == y_ingreso else 1
            m_end = 12  # Hasta diciembre: incluye todos los meses pendientes del año
            for m in range(m_start, m_end + 1):
                if (y, m) > (hoy.year, 12):
                    break
                if _mes_periodo_ya_pagado(trabajador, y, m, "mes"):
                    continue
                key = (y, m)
                if key not in vistos:
                    vistos.add(key)
                    opciones.append((f"{y}-{m:02d}", f"{MESES_NOMBRES[m - 1]} {y}"))
    if incluir_mes_edicion and incluir_mes_edicion not in vistos:
        y, m = incluir_mes_edicion
        opciones.insert(0, (f"{y}-{m:02d}", f"{MESES_NOMBRES[m - 1]} {y} (editando)"))
    return sorted(opciones, key=lambda x: x[0])  # Ascendente: el más antiguo primero (próximo a pagar)


def _mes_periodo_ya_pagado(
    trabajador: Trabajador,
    year: int,
    month: int,
    periodo_referencia: str,
    excluir_pago_id: int | None = None,
) -> bool:
    """Devuelve True si ese periodo del mes ya está pagado (no se puede volver a pagar)."""
    qs = PagoTrabajador.objects.filter(
        trabajador=trabajador,
        fecha_pago__year=year,
        fecha_pago__month=month,
    )
    if excluir_pago_id:
        qs = qs.exclude(pk=excluir_pago_id)
    if periodo_referencia == "mes":
        if qs.filter(periodo_referencia="mes").exists():
            return True
        q1 = qs.filter(periodo_referencia="quincena_1").exists()
        q2 = qs.filter(periodo_referencia="quincena_2").exists()
        return q1 and q2
    if periodo_referencia == "quincena_1":
        return qs.filter(periodo_referencia__in=["quincena_1", "mes"]).exists()
    if periodo_referencia == "quincena_2":
        return qs.filter(periodo_referencia__in=["quincena_2", "mes"]).exists()
    return False


def _quincenas_pendientes(trabajador: Trabajador, limite_meses=36):
    """Devuelve qué quincenas faltan por pagar por mes. Recorre año por año desde fecha_ingreso."""
    tiene_quincenal = (
        trabajador.periodo_pago == "quincenal"
        or trabajador.pagos.filter(periodo_referencia__in=["quincena_1", "quincena_2", "mes"]).exists()
    )
    if not tiene_quincenal:
        return []
    hoy = timezone.localdate()
    fecha_ingreso = trabajador.fecha_ingreso
    if not fecha_ingreso:
        fecha_ingreso = hoy
    y_ingreso, m_ingreso = fecha_ingreso.year, fecha_ingreso.month
    MESES = (
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    )
    # Recorrer todos los meses desde fecha_ingreso hasta fin del año actual (incluye meses futuros pendientes)
    meses_a_revisar = []
    y, m = y_ingreso, m_ingreso
    count = 0
    while (y, m) <= (hoy.year, 12) and count < limite_meses:
        meses_a_revisar.append((y, m))
        count += 1
        m += 1
        if m > 12:
            m = 1
            y += 1
    meses_ordenados = sorted(meses_a_revisar, key=lambda x: (x[0], x[1]), reverse=True)
    resultado = []
    for y, m in meses_ordenados[:limite_meses]:
        pagos_mes = PagoTrabajador.objects.filter(
            trabajador=trabajador,
            fecha_pago__year=y,
            fecha_pago__month=m,
        )
        q1 = pagos_mes.filter(periodo_referencia__in=["quincena_1", "mes"]).exists()
        q2 = pagos_mes.filter(periodo_referencia__in=["quincena_2", "mes"]).exists()
        pendientes = []
        if not q1:
            pendientes.append("Quincena 1")
        if not q2:
            pendientes.append("Quincena 2")
        if pendientes:
            resultado.append({
                "year": y,
                "month": m,
                "label": f"{MESES[m - 1]} {y}",
                "fecha_pago_q1": date(y, m, 1),
                "fecha_pago_q2": date(y, m, 16),
                "pendientes": pendientes,
                "mes_completo": False,
            })
        else:
            resultado.append({
                "year": y,
                "month": m,
                "label": f"{MESES[m - 1]} {y}",
                "pendientes": [],
                "mes_completo": True,
            })
    return resultado


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
        ctx["pagos_recientes"] = t.pagos.select_related("usuario_registro").order_by("-fecha_pago", "-id")[:20]
        ctx["sueldos_recientes"] = t.sueldos.select_related("usuario_registro").order_by("-fecha_inicio")[:6]
        ctx["asistencias_recientes"] = t.asistencias.order_by("-fecha_hora_ingreso")[:8]
        qp = _quincenas_pendientes(t)
        ctx["quincenas_pendientes"] = sorted(qp, key=lambda x: (x["year"], x["month"]))
        ctx["total_quincenas_pendientes"] = sum(len(q["pendientes"]) for q in qp)
        ctx["adelantos_recientes"] = t.adelantos.order_by("-fecha")[:8]
        ctx["descuentos_recientes"] = t.descuentos.order_by("-fecha")[:8]
        ctx["total_adelantos"] = t.adelantos.aggregate(t=Sum("monto"))["t"] or 0
        ctx["total_descuentos"] = t.descuentos.aggregate(t=Sum("monto"))["t"] or 0
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
    form_class = PagoTrabajadorCreateForm
    template_name = "trabajadores/pago_form.html"
    required_perms = ["trabajadores.pagos.create"]

    def dispatch(self, request, *args, **kwargs):
        self.trabajador = get_object_or_404(Trabajador, pk=self.kwargs["trabajador_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["meses_opciones"] = _meses_pendientes_opciones(self.trabajador)
        return kwargs

    def get_initial(self):
        from decimal import Decimal
        initial = super().get_initial()
        meses_opciones = _meses_pendientes_opciones(self.trabajador)
        if meses_opciones:
            initial["mes_a_pagar"] = meses_opciones[0][0]
        hoy = timezone.localdate()
        if self.trabajador.periodo_pago == "quincenal":
            dia = hoy.day
            initial["periodo_referencia"] = "quincena_2" if dia >= 16 else "quincena_1"
            # Monto por quincena = mitad del sueldo
            sueldo = self.trabajador.sueldo_mensual or Decimal("0")
            initial["monto"] = (sueldo / 2).quantize(Decimal("0.01"))
        else:
            initial["periodo_referencia"] = "mes"
            initial["monto"] = self.trabajador.sueldo_mensual or Decimal("0")
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajador"] = self.trabajador
        ctx["quincenas_pendientes"] = _quincenas_pendientes(self.trabajador)
        return ctx

    def form_valid(self, form):
        pr = form.cleaned_data.get("periodo_referencia")
        mes_val = form.cleaned_data.get("mes_a_pagar")
        if mes_val:
            parts = mes_val.split("-")
            if len(parts) == 2:
                y, m = int(parts[0]), int(parts[1])
                if _mes_periodo_ya_pagado(self.trabajador, y, m, pr):
                    messages.error(
                        self.request,
                        f"Ese mes ya está pagado. {MESES_NOMBRES[m - 1]} {y} tiene registrado el periodo indicado.",
                    )
                    return self.form_invalid(form)
                dia = 16 if pr == "quincena_2" else 1
                form.instance.fecha_pago = date(y, m, dia)
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
        ctx["quincenas_pendientes"] = _quincenas_pendientes(self.trabajador)
        return ctx

    def form_valid(self, form):
        fd = form.cleaned_data.get("fecha_pago")
        pr = form.cleaned_data.get("periodo_referencia")
        if fd and pr and _mes_periodo_ya_pagado(
            self.trabajador, fd.year, fd.month, pr, excluir_pago_id=self.object.pk
        ):
            MESES = (
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            )
            mes_nom = MESES[fd.month - 1] if 1 <= fd.month <= 12 else str(fd.month)
            messages.error(
                self.request,
                f"Ese mes ya está pagado. {mes_nom} {fd.year} tiene registrado el periodo indicado. "
                "No se puede volver a pagar.",
            )
            return self.form_invalid(form)
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajador"] = self.trabajador
        return ctx

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


# ============== Adelantos ==============


class AdelantoTrabajadorListView(RolePermissionRequiredMixin, ListView):
    model = AdelantoTrabajador
    template_name = "trabajadores/adelanto_list.html"
    context_object_name = "adelantos"
    paginate_by = 20
    required_perms = ["trabajadores.pagos.view"]

    def get_queryset(self):
        self.trabajador = get_object_or_404(Trabajador, pk=self.kwargs["trabajador_id"])
        return AdelantoTrabajador.objects.filter(trabajador=self.trabajador).select_related("usuario_registro")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajador"] = self.trabajador
        ctx["total_adelantos"] = self.get_queryset().aggregate(t=Sum("monto"))["t"] or 0
        return ctx


class AdelantoTrabajadorCreateView(RolePermissionRequiredMixin, CreateView):
    model = AdelantoTrabajador
    form_class = AdelantoTrabajadorForm
    template_name = "trabajadores/adelanto_form.html"
    required_perms = ["trabajadores.pagos.create"]

    def dispatch(self, request, *args, **kwargs):
        self.trabajador = get_object_or_404(Trabajador, pk=self.kwargs["trabajador_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        hoy = timezone.localdate()
        initial["fecha"] = hoy
        initial["mes_ref"] = hoy.month
        initial["anio_ref"] = hoy.year
        return initial

    def form_valid(self, form):
        form.instance.trabajador = self.trabajador
        form.instance.usuario_registro = self.request.user
        messages.success(self.request, "Adelanto registrado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajador"] = self.trabajador
        return ctx

    def get_success_url(self):
        return reverse("trabajadores:adelanto_list", args=[self.trabajador.pk])


class AdelantoTrabajadorDeleteView(RolePermissionRequiredMixin, DeleteView):
    model = AdelantoTrabajador
    template_name = "trabajadores/adelanto_confirm_delete.html"
    required_perms = ["trabajadores.pagos.update"]

    def get_queryset(self):
        return AdelantoTrabajador.objects.filter(trabajador_id=self.kwargs["trabajador_id"])

    def get_success_url(self):
        return reverse("trabajadores:adelanto_list", args=[self.object.trabajador_id])

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Adelanto eliminado.")
        return super().delete(request, *args, **kwargs)


# ============== Descuentos ==============


class DescuentoTrabajadorListView(RolePermissionRequiredMixin, ListView):
    model = DescuentoTrabajador
    template_name = "trabajadores/descuento_list.html"
    context_object_name = "descuentos"
    paginate_by = 20
    required_perms = ["trabajadores.pagos.view"]

    def get_queryset(self):
        self.trabajador = get_object_or_404(Trabajador, pk=self.kwargs["trabajador_id"])
        return DescuentoTrabajador.objects.filter(trabajador=self.trabajador).select_related("usuario_registro")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajador"] = self.trabajador
        ctx["total_descuentos"] = self.get_queryset().aggregate(t=Sum("monto"))["t"] or 0
        return ctx


class DescuentoTrabajadorCreateView(RolePermissionRequiredMixin, CreateView):
    model = DescuentoTrabajador
    form_class = DescuentoTrabajadorForm
    template_name = "trabajadores/descuento_form.html"
    required_perms = ["trabajadores.pagos.create"]

    def dispatch(self, request, *args, **kwargs):
        self.trabajador = get_object_or_404(Trabajador, pk=self.kwargs["trabajador_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        hoy = timezone.localdate()
        initial["fecha"] = hoy
        initial["mes_ref"] = hoy.month
        initial["anio_ref"] = hoy.year
        return initial

    def form_valid(self, form):
        form.instance.trabajador = self.trabajador
        form.instance.usuario_registro = self.request.user
        messages.success(self.request, "Descuento registrado correctamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajador"] = self.trabajador
        return ctx

    def get_success_url(self):
        return reverse("trabajadores:descuento_list", args=[self.trabajador.pk])


class DescuentoTrabajadorDeleteView(RolePermissionRequiredMixin, DeleteView):
    model = DescuentoTrabajador
    template_name = "trabajadores/descuento_confirm_delete.html"
    required_perms = ["trabajadores.pagos.update"]

    def get_queryset(self):
        return DescuentoTrabajador.objects.filter(trabajador_id=self.kwargs["trabajador_id"])

    def get_success_url(self):
        return reverse("trabajadores:descuento_list", args=[self.object.trabajador_id])

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Descuento eliminado.")
        return super().delete(request, *args, **kwargs)


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


# ============== Asistencia de personal ==============


class AsistenciaTrabajadorListView(RolePermissionRequiredMixin, ListView):
    """Listado de asistencias de personal con filtros."""
    model = AsistenciaTrabajador
    template_name = "trabajadores/asistencia_list.html"
    context_object_name = "asistencias"
    paginate_by = 30
    required_perms = ["trabajadores.asistencia.view"]

    def get_queryset(self):
        qs = AsistenciaTrabajador.objects.select_related("trabajador")
        f_date = self.request.GET.get("fecha", "").strip()
        f_trabajador = self.request.GET.get("trabajador", "").strip()
        if f_date:
            try:
                d = timezone.datetime.strptime(f_date, "%Y-%m-%d").date()
                qs = qs.filter(fecha_hora_ingreso__date=d)
            except ValueError:
                pass
        if f_trabajador:
            qs = qs.filter(trabajador_id=f_trabajador)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajadores"] = Trabajador.objects.filter(estado="activo")
        ctx["f_fecha"] = self.request.GET.get("fecha", "")
        ctx["f_trabajador"] = self.request.GET.get("trabajador", "")
        return ctx


class AsistenciaTrabajadorTrabajadorListView(RolePermissionRequiredMixin, ListView):
    """Listado de asistencias de un trabajador."""
    model = AsistenciaTrabajador
    template_name = "trabajadores/asistencia_trabajador_list.html"
    context_object_name = "asistencias"
    paginate_by = 20
    required_perms = ["trabajadores.asistencia.view"]

    def get_queryset(self):
        self.trabajador = get_object_or_404(Trabajador, pk=self.kwargs["trabajador_id"])
        return AsistenciaTrabajador.objects.filter(trabajador=self.trabajador)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["trabajador"] = self.trabajador
        return ctx


class AsistenciaTrabajadorRegistroRapidoView(RolePermissionRequiredMixin, View):
    """Registro rápido: buscar por documento o seleccionar trabajador, marcar ingreso o término."""
    required_perms = ["trabajadores.asistencia.create"]

    def get(self, request):
        doc = request.GET.get("doc", "").strip()
        trab_id = request.GET.get("trabajador_id", "").strip()
        trabajador = None
        if trab_id:
            trabajador = Trabajador.objects.filter(pk=trab_id, estado="activo").first()
        if not trabajador and doc:
            trabajador = Trabajador.objects.filter(
                documento__iexact=doc, estado="activo"
            ).first()
        ultima_abierta = None
        if trabajador:
            ultima_abierta = AsistenciaTrabajador.objects.filter(
                trabajador=trabajador, fecha_hora_termino__isnull=True
            ).order_by("-fecha_hora_ingreso").first()
        return render(request, "trabajadores/asistencia_registro_rapido.html", {
            "doc": doc,
            "trabajador": trabajador,
            "ultima_abierta": ultima_abierta,
            "trabajadores": Trabajador.objects.filter(estado="activo").order_by("apellidos", "nombres"),
        })

    def post(self, request):
        accion = request.POST.get("accion")
        trabajador_id = request.POST.get("trabajador_id", "").strip()
        doc = request.POST.get("doc", "").strip()

        trabajador = None
        if trabajador_id:
            trabajador = Trabajador.objects.filter(pk=trabajador_id, estado="activo").first()
        if not trabajador and doc:
            trabajador = Trabajador.objects.filter(documento__iexact=doc, estado="activo").first()

        if not trabajador:
            messages.error(request, "Seleccione un trabajador activo o ingrese un documento válido.")
            return redirect("trabajadores:asistencia_rapido")

        ultima_abierta = AsistenciaTrabajador.objects.filter(
            trabajador=trabajador, fecha_hora_termino__isnull=True
        ).order_by("-fecha_hora_ingreso").first()

        if accion == "registrar_ingreso":
            AsistenciaTrabajador.objects.create(
                trabajador=trabajador,
                fecha_hora_ingreso=timezone.now(),
            )
            messages.success(request, f"Ingreso registrado para {trabajador.nombre_completo}.")
            return redirect("trabajadores:asistencia_rapido")

        if accion == "marcar_termino" and ultima_abierta:
            ultima_abierta.fecha_hora_termino = timezone.now()
            ultima_abierta.save()
            messages.success(request, f"Término registrado para {trabajador.nombre_completo}.")
            return redirect("trabajadores:asistencia_rapido")

        if accion == "marcar_termino" and not ultima_abierta:
            messages.warning(request, f"{trabajador.nombre_completo} no tiene jornada abierta para cerrar.")
            return redirect("trabajadores:asistencia_rapido")

        return redirect("trabajadores:asistencia_rapido")


class AsistenciaTrabajadorUpdateView(RolePermissionRequiredMixin, UpdateView):
    """Editar asistencia (ingreso/término)."""
    model = AsistenciaTrabajador
    form_class = AsistenciaTrabajadorForm
    template_name = "trabajadores/asistencia_form.html"
    context_object_name = "asistencia"
    required_perms = ["trabajadores.asistencia.create"]

    def get_success_url(self):
        return reverse("trabajadores:asistencia_list")

