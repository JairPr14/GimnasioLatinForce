from django import forms
from .models import Venta


class VentaForm(forms.ModelForm):
    """Formulario cabecera de venta (Nueva venta)."""

    class Meta:
        model = Venta
        fields = [
            'cliente', 'fecha_emision', 'fecha_vencimiento',
            'tipo_comprobante', 'serie', 'tipo_operacion',
            'descuento_global', 'es_proforma', 'observaciones', 'condicion_pago'
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'fecha_emision': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'fecha_vencimiento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'tipo_comprobante': forms.Select(attrs={'class': 'form-select'}),
            'serie': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_operacion': forms.Select(attrs={'class': 'form-select'}),
            'descuento_global': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}
            ),
            'es_proforma': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'condicion_pago': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from clientes.models import Cliente
        self.fields['cliente'].queryset = Cliente.objects.filter(
            estado__in=('activo', 'suspendido')
        ).order_by('apellidos', 'nombres')
        self.fields['cliente'].required = False
        self.fields['fecha_vencimiento'].required = False
        self.fields['observaciones'].required = False
        self.fields['condicion_pago'].required = False
        self.fields['fecha_emision'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_vencimiento'].input_formats = ['%Y-%m-%d']
