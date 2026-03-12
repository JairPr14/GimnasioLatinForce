"""
Formularios del módulo Clientes.
"""
from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    """Formulario para crear/editar cliente."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El input type="date" requiere valor en YYYY-MM-DD para mostrarlo y guardarlo bien.
        self.fields['fecha_inscripcion'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']

    class Meta:
        model = Cliente
        fields = [
            'nombres', 'apellidos', 'dni', 'telefono', 'correo', 'direccion',
            'fecha_inscripcion', 'fecha_nacimiento', 'contacto_emergencia', 'estado', 'foto',
            'observaciones_medicas'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fecha_inscripcion': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'},
            ),
            'fecha_nacimiento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'},
            ),
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre y teléfono'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'observaciones_medicas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Restricciones físicas, alergias, condiciones médicas...'
            }),
        }
