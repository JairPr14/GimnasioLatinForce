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

    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="pagos")
    fecha_pago = models.DateField()
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

