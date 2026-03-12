from __future__ import annotations

from django import forms

from .models import PagoTrabajador, SueldoHistorial, Trabajador


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
            "estado": forms.Select(attrs={"class": "form-select"}),
            "fecha_ingreso": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class PagoTrabajadorForm(forms.ModelForm):
    class Meta:
        model = PagoTrabajador
        fields = (
            "fecha_pago",
            "monto",
            "metodo_pago",
            "concepto",
            "numero_comprobante",
            "observaciones",
        )
        widgets = {
            "fecha_pago": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "metodo_pago": forms.Select(attrs={"class": "form-select"}),
            "concepto": forms.TextInput(attrs={"class": "form-control"}),
            "numero_comprobante": forms.TextInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class SueldoHistorialForm(forms.ModelForm):
    class Meta:
        model = SueldoHistorial
        fields = ("fecha_inicio", "sueldo_mensual", "motivo")
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "sueldo_mensual": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "motivo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: aumento, ajuste, ingreso..."}),
        }

