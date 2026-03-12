"""
Modelos del módulo Clientes.
"""
from django.db import models


class Cliente(models.Model):
    """Cliente del gimnasio."""

    ESTADO = [
        ('activo', 'Activo'),
        ('suspendido', 'Suspendido'),
        ('retirado', 'Retirado'),
    ]

    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True, verbose_name='DNI o documento')
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    fecha_inscripcion = models.DateField()
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de nacimiento')
    contacto_emergencia = models.CharField(max_length=200, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO, default='activo')
    foto = models.ImageField(upload_to='clientes/fotos/', blank=True, null=True)
    observaciones_medicas = models.TextField(
        blank=True,
        verbose_name='Observaciones médicas o restricciones físicas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['apellidos', 'nombres']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.apellidos} {self.nombres}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
