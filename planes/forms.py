"""
Formularios del módulo Planes.
"""
from django import forms
from .models import Plan


class PlanForm(forms.ModelForm):
    """Formulario para crear/editar plan."""

    class Meta:
        model = Plan
        fields = [
            'nombre', 'tipo_periodo', 'duracion_dias', 'precio',
            'es_promocion', 'descripcion_promocion',
            'fecha_inicio_vigencia', 'fecha_vencimiento_vigencia',
            'renovacion', 'dias_gracia_mora', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_periodo': forms.Select(attrs={'class': 'form-select'}),
            'duracion_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'es_promocion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'descripcion_promocion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Detalles de la promoción...'
            }),
            'fecha_inicio_vigencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_vencimiento_vigencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'renovacion': forms.Select(attrs={'class': 'form-select'}),
            'dias_gracia_mora': forms.NumberInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
