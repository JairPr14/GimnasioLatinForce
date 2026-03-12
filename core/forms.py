"""
Formularios del módulo core.
"""
from django import forms
from .models import ConfiguracionEmpresa


class ConfiguracionEmpresaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEmpresa
        fields = ['logo']
        widgets = {
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
