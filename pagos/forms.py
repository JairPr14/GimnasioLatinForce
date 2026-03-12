"""
Formularios del módulo Pagos.
"""
from django import forms
from .models import Pago, Deuda
from clientes.models import Cliente


class PagoForm(forms.ModelForm):
    """Formulario para registrar pago."""

    class Meta:
        model = Pago
        fields = [
            'cliente', 'plan', 'deuda', 'monto', 'metodo_pago',
            'fecha_pago', 'concepto', 'numero_comprobante', 'observaciones'
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'deuda': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'fecha_pago': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'concepto': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_comprobante': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'Se genera automáticamente'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(estado__in=('activo', 'suspendido'))
        from planes.models import Plan
        self.fields['plan'].queryset = Plan.objects.filter(activo=True)
        self.fields['plan'].label_from_instance = lambda p: f"{p.nombre} ({p.get_tipo_periodo_display()}) - S/ {p.precio}"
        self.fields['plan'].required = False
        self.fields['deuda'].required = False
        from django.db.models import Sum, F, Value, DecimalField
        from django.db.models.functions import Coalesce
        deudas_pendientes = Deuda.objects.annotate(
            abonado=Coalesce(Sum('pago__monto'), Value(0, output_field=DecimalField()))
        ).filter(monto__gt=F('abonado'))
        self.fields['deuda'].queryset = deudas_pendientes
        self.fields['numero_comprobante'].required = False
        self.fields['observaciones'].required = False
        self.fields['fecha_pago'].input_formats = ['%Y-%m-%d']


class DeudaForm(forms.ModelForm):
    """Formulario para registrar deuda."""

    class Meta:
        model = Deuda
        fields = ['cliente', 'monto', 'descripcion', 'fecha_vencimiento']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(estado__in=('activo', 'suspendido'))
        self.fields['fecha_vencimiento'].required = False
