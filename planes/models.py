"""
Modelos del módulo Planes.
"""
from django.db import models


class Plan(models.Model):
    """Plan de membresía del gimnasio."""

    TIPO_PERIODO = [
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual'),
    ]

    RENOVACION = [
        ('automatica', 'Automática'),
        ('manual', 'Manual'),
    ]

    nombre = models.CharField(max_length=100)
    tipo_periodo = models.CharField(max_length=20, choices=TIPO_PERIODO)
    duracion_dias = models.PositiveIntegerField(
        help_text='Duración en días (7=semanal, 15=quincenal, 30=mensual, 365=anual)'
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    es_promocion = models.BooleanField(default=False, verbose_name='Es promoción')
    descripcion_promocion = models.TextField(blank=True, verbose_name='Detalle de promoción')
    fecha_inicio_vigencia = models.DateField(
        null=True, blank=True,
        verbose_name='Fecha inicio vigencia (opcional)'
    )
    fecha_vencimiento_vigencia = models.DateField(
        null=True, blank=True,
        verbose_name='Fecha vencimiento vigencia (opcional)'
    )
    renovacion = models.CharField(
        max_length=20,
        choices=RENOVACION,
        default='manual',
        verbose_name='Renovación'
    )
    dias_gracia_mora = models.PositiveIntegerField(
        default=0,
        verbose_name='Días de gracia (mora)',
        help_text='Días después del vencimiento antes de considerar en mora'
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_periodo_display()})"
