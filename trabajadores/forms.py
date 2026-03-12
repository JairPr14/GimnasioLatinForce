from __future__ import annotations

from django import forms

from .models import AdelantoTrabajador, AsistenciaTrabajador, DescuentoTrabajador, PagoTrabajador, SueldoHistorial, Trabajador


class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = (
            "nombres",
            "apellidos",
            "documento",
            "telefono",
            "correo",
            "direccion",
            "cargo",
            "sueldo_mensual",
            "periodo_pago",
            "estado",
            "fecha_ingreso",
        )
        widgets = {
            "nombres": forms.TextInput(attrs={"class": "form-control"}),
            "apellidos": forms.TextInput(attrs={"class": "form-control"}),
            "documento": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "correo": forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "cargo": forms.TextInput(attrs={"class": "form-control"}),
            "sueldo_mensual": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "periodo_pago": forms.Select(attrs={"class": "form-select"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
            "fecha_ingreso": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class PagoTrabajadorForm(forms.ModelForm):
    class Meta:
        model = PagoTrabajador
        fields = (
            "fecha_pago",
            "periodo_referencia",
            "monto",
            "metodo_pago",
            "concepto",
            "numero_comprobante",
            "observaciones",
        )
        widgets = {
            "fecha_pago": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "periodo_referencia": forms.Select(attrs={"class": "form-select"}),
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "metodo_pago": forms.Select(attrs={"class": "form-select"}),
            "concepto": forms.TextInput(attrs={"class": "form-control"}),
            "numero_comprobante": forms.TextInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class PagoTrabajadorCreateForm(PagoTrabajadorForm):
    """Formulario de registro: selecciona mes pendiente y periodo en vez de fecha libre."""
    mes_a_pagar = forms.ChoiceField(
        label="Mes a pagar",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta(PagoTrabajadorForm.Meta):
        fields = (
            "mes_a_pagar",
            "periodo_referencia",
            "monto",
            "metodo_pago",
            "concepto",
            "numero_comprobante",
            "observaciones",
        )

    def __init__(self, meses_opciones=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("fecha_pago", None)
        self.fields["mes_a_pagar"].choices = [("", "—— Seleccione mes ——")] + (meses_opciones or [])


class SueldoHistorialForm(forms.ModelForm):
    class Meta:
        model = SueldoHistorial
        fields = ("fecha_inicio", "sueldo_mensual", "motivo")
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "sueldo_mensual": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "motivo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: aumento, ajuste, ingreso..."}),
        }


class AsistenciaTrabajadorForm(forms.ModelForm):
    class Meta:
        model = AsistenciaTrabajador
        fields = ("trabajador", "fecha_hora_ingreso", "fecha_hora_termino")
        widgets = {
            "trabajador": forms.Select(attrs={"class": "form-select"}),
            "fecha_hora_ingreso": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "fecha_hora_termino": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha_hora_ingreso"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
        self.fields["fecha_hora_termino"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"]


class AdelantoTrabajadorForm(forms.ModelForm):
    class Meta:
        model = AdelantoTrabajador
        fields = ("fecha", "monto", "descontar_de", "mes_ref", "anio_ref", "observaciones")
        widgets = {
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "descontar_de": forms.Select(attrs={"class": "form-select"}),
            "mes_ref": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 12, "placeholder": "1-12"}),
            "anio_ref": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ej: 2026"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class DescuentoTrabajadorForm(forms.ModelForm):
    class Meta:
        model = DescuentoTrabajador
        fields = ("fecha", "monto", "tipo", "periodo_referencia", "mes_ref", "anio_ref", "observaciones")
        widgets = {
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "periodo_referencia": forms.Select(attrs={"class": "form-select"}),
            "mes_ref": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 12}),
            "anio_ref": forms.NumberInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

