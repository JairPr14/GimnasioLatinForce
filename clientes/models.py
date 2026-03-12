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


class Asistencia(models.Model):
    """Registro de asistencia de cliente (ingreso/egreso al gimnasio)."""

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='asistencias')
    fecha_hora_ingreso = models.DateTimeField(verbose_name='Hora de ingreso')
    fecha_hora_egreso = models.DateTimeField(null=True, blank=True, verbose_name='Hora de egreso')
    duracion_minutos_defecto = 90  # 1.5 horas

    class Meta:
        ordering = ['-fecha_hora_ingreso']
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'

    def __str__(self):
        return f"{self.cliente} — {self.fecha_hora_ingreso.strftime('%d/%m/%Y %H:%M')}"

    @property
    def hora_egreso_efectiva(self):
        """Egreso real o calculado (1.5h después del ingreso si no marcó salida)."""
        if self.fecha_hora_egreso:
            return self.fecha_hora_egreso
        from datetime import timedelta
        from django.utils import timezone
        limite = self.fecha_hora_ingreso + timedelta(minutes=self.duracion_minutos_defecto)
        if timezone.now() >= limite:
            return limite
        return None  # Aún dentro, no ha salido

    @property
    def cerrada(self):
        """True si ya salió (manual o por defecto 1.5h)."""
        return self.hora_egreso_efectiva is not None


class AsistenciaInvitado(models.Model):
    """Invitado que ingresa con un cliente (máx 3 por mes, cliente con plan)."""

    asistencia = models.ForeignKey(
        Asistencia, on_delete=models.CASCADE, related_name='invitados'
    )
    nombre = models.CharField(max_length=120, verbose_name='Nombre del invitado')
    documento = models.CharField(max_length=20, blank=True, verbose_name='DNI (opcional)')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = 'Invitado'
        verbose_name_plural = 'Invitados'

    def __str__(self):
        return f"{self.nombre} (invitado de {self.asistencia.cliente})"
