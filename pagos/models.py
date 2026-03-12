"""
Modelos del módulo Pagos.
"""
from django.conf import settings
from django.db import models
from django.db.models import Sum

from clientes.models import Cliente
from planes.models import Plan


class Deuda(models.Model):
    """Deuda pendiente de un cliente."""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=200)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Deuda'
        verbose_name_plural = 'Deudas'

    def __str__(self):
        return f"{self.cliente} - S/ {self.monto}"

    @property
    def monto_abonado(self):
        return self.pago_set.aggregate(total=Sum('monto'))['total'] or 0

    @property
    def monto_pendiente(self):
        return self.monto - self.monto_abonado

    @property
    def saldada(self):
        return self.monto_pendiente <= 0


class Pago(models.Model):
    """Registro de pago."""
    METODO = [
        ('efectivo', 'Efectivo'),
        ('yape', 'Yape'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    plan = models.ForeignKey(
        Plan, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Plan que paga'
    )
    deuda = models.ForeignKey(Deuda, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Abono a deuda')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO)
    fecha_pago = models.DateField()
    concepto = models.CharField(max_length=200)
    numero_comprobante = models.CharField(max_length=50, blank=True)
    observaciones = models.TextField(blank=True)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pagos_registrados'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_pago', '-fecha_creacion']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"{self.cliente} - S/ {self.monto} ({self.fecha_pago})"
