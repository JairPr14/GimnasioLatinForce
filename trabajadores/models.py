from __future__ import annotations

from django.conf import settings
from django.db import models


class Trabajador(models.Model):
    ESTADO = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
    ]

    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    documento = models.CharField(max_length=20, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    correo = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)

    cargo = models.CharField(max_length=80, blank=True)
    sueldo_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    periodo_pago = models.CharField(
        max_length=20,
        choices=[
            ("quincenal", "Quincenal"),
            ("mensual", "Mensual"),
        ],
        default="mensual",
        verbose_name="Periodo de pago",
    )
    estado = models.CharField(max_length=20, choices=ESTADO, default="activo")

    fecha_ingreso = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["apellidos", "nombres"]
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()

    def __str__(self) -> str:
        return self.nombre_completo


class PagoTrabajador(models.Model):
    METODO = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
        ("yape", "Yape"),
        ("plin", "Plin"),
        ("tarjeta", "Tarjeta"),
    ]
    PERIODO_REF = [
        ("quincena_1", "Quincena 1"),
        ("quincena_2", "Quincena 2"),
        ("mes", "Mes completo"),
    ]

    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="pagos")
    fecha_pago = models.DateField()
    periodo_referencia = models.CharField(
        max_length=20,
        choices=PERIODO_REF,
        default="mes",
        verbose_name="Periodo referido",
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO, default="efectivo")
    concepto = models.CharField(max_length=200, blank=True)
    numero_comprobante = models.CharField(max_length=50, blank=True)
    observaciones = models.TextField(blank=True)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pagos_trabajadores_registrados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_pago", "-id"]
        verbose_name = "Pago a trabajador"
        verbose_name_plural = "Pagos a trabajadores"

    def __str__(self) -> str:
        return f"{self.trabajador} - S/ {self.monto} ({self.fecha_pago})"


class AsistenciaTrabajador(models.Model):
    """Registro de asistencia de personal: hora de ingreso y término."""

    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="asistencias")
    fecha_hora_ingreso = models.DateTimeField(verbose_name="Hora de ingreso")
    fecha_hora_termino = models.DateTimeField(null=True, blank=True, verbose_name="Hora de término")

    class Meta:
        ordering = ["-fecha_hora_ingreso"]
        verbose_name = "Asistencia de trabajador"
        verbose_name_plural = "Asistencias de trabajadores"

    def __str__(self) -> str:
        return f"{self.trabajador} — {self.fecha_hora_ingreso.strftime('%d/%m/%Y %H:%M')}"

    @property
    def cerrada(self) -> bool:
        return self.fecha_hora_termino is not None


class SueldoHistorial(models.Model):
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="sueldos")
    fecha_inicio = models.DateField()
    sueldo_mensual = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.CharField(max_length=160, blank=True)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sueldos_trabajadores_registrados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_inicio", "-id"]
        verbose_name = "Historial de sueldo"
        verbose_name_plural = "Historial de sueldos"

    def __str__(self) -> str:
        return f"{self.trabajador} - S/ {self.sueldo_mensual} desde {self.fecha_inicio}"


class AdelantoTrabajador(models.Model):
    """Adelanto de sueldo: se descontará de una o ambas quincenas."""

    DESCONTAR_DE = [
        ("ambas_quincenas", "Ambas quincenas"),
        ("quincena_1", "Solo quincena 1"),
        ("quincena_2", "Solo quincena 2"),
    ]

    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="adelantos")
    fecha = models.DateField(verbose_name="Fecha del adelanto")
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descontar_de = models.CharField(
        max_length=20,
        choices=DESCONTAR_DE,
        default="ambas_quincenas",
        verbose_name="Descontar de",
    )
    mes_ref = models.PositiveSmallIntegerField(verbose_name="Mes de referencia", null=True, blank=True)
    anio_ref = models.PositiveSmallIntegerField(verbose_name="Año de referencia", null=True, blank=True)
    observaciones = models.TextField(blank=True)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="adelantos_trabajadores_registrados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "Adelanto a trabajador"
        verbose_name_plural = "Adelantos a trabajadores"

    def __str__(self) -> str:
        return f"{self.trabajador} - S/ {self.monto} adelanto ({self.fecha})"


class DescuentoTrabajador(models.Model):
    """Descuento: tardanzas, AFP, ONP, incumplimientos. AFP y ONP aplican a ambas quincenas."""

    TIPO = [
        ("tardanzas", "Tardanzas"),
        ("afp", "AFP"),
        ("onp", "ONP"),
        ("incumplimientos", "Incumplimientos"),
    ]
    PERIODO_REF = [
        ("quincena_1", "Quincena 1"),
        ("quincena_2", "Quincena 2"),
        ("ambas", "Ambas quincenas"),
    ]

    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="descuentos")
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    tipo = models.CharField(max_length=20, choices=TIPO)
    periodo_referencia = models.CharField(
        max_length=20,
        choices=PERIODO_REF,
        default="quincena_1",
        verbose_name="Periodo referido",
    )
    mes_ref = models.PositiveSmallIntegerField(verbose_name="Mes de referencia", null=True, blank=True)
    anio_ref = models.PositiveSmallIntegerField(verbose_name="Año de referencia", null=True, blank=True)
    observaciones = models.TextField(blank=True)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="descuentos_trabajadores_registrados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "Descuento a trabajador"
        verbose_name_plural = "Descuentos a trabajadores"

    def __str__(self) -> str:
        return f"{self.trabajador} - S/ {self.monto} {self.get_tipo_display()} ({self.fecha})"

    def save(self, *args, **kwargs):
        if self.tipo in ("afp", "onp"):
            self.periodo_referencia = "ambas"
        super().save(*args, **kwargs)

