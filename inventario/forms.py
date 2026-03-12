from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Código autogenerado al crear: no obligar al usuario a escribirlo.
        self.fields['codigo'].required = False
        self.fields['codigo'].widget.attrs.update({
            'readonly': True,
            'class': (self.fields['codigo'].widget.attrs.get('class', '') + ' bg-light').strip(),
            'placeholder': 'Se genera automáticamente',
        })

    class Meta:
        model = Producto
        fields = [
            'nombre', 'codigo', 'codigo_barras', 'descripcion',
            'precio', 'stock', 'unidad', 'activo', 'permitir_vender_sin_stock'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'unidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UND'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'permitir_vender_sin_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
