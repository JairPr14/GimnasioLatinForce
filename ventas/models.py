"""
Modelos del módulo Ventas.
"""
from django.conf import settings
from django.db import models
from decimal import Decimal

from clientes.models import Cliente
from inventario.models import Producto


class Venta(models.Model):
    """Comprobante de venta (boleta, proforma, etc.)."""

    TIPO_COMPROBANTE = [
        ('boleta', 'Boleta de Venta Electrónica'),
        ('factura', 'Factura Electrónica'),
        ('proforma', 'Proforma'),
    ]

    TIPO_OPERACION = [
        ('venta_interna', 'VENTA INTERNA'),
        ('venta_externa', 'VENTA EXTERNA'),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ventas'
    )
    fecha_emision = models.DateField(verbose_name='Fecha de emisión')
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de vcto.')
    tipo_comprobante = models.CharField(
        max_length=20, choices=TIPO_COMPROBANTE, default='boleta'
    )
    serie = models.CharField(max_length=10, default='BB01')
    numero_comprobante = models.CharField(max_length=20, blank=True)
    tipo_operacion = models.CharField(
        max_length=20, choices=TIPO_OPERACION, default='venta_interna'
    )
    descuento_global = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0'),
        verbose_name='Dscto. global (%)'
    )
    es_proforma = models.BooleanField(default=False, verbose_name='PROFORMA')
    observaciones = models.TextField(blank=True)
    condicion_pago = models.CharField(max_length=100, blank=True, verbose_name='Cond. pago')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='ventas_registradas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[('borrador', 'Borrador'), ('emitido', 'Emitido'), ('anulado', 'Anulado')],
        default='emitido'
    )

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'

    def __str__(self):
        return f"{self.get_tipo_comprobante_display()} {self.serie}-{self.numero_comprobante or '—'}"

    def recalcular_totales(self):
        subtotal = sum(d.subtotal for d in self.detalles.all())
        desc = (self.descuento_global or Decimal('0')) / Decimal('100')
        self.subtotal = subtotal
        self.total = subtotal * (Decimal('1') - desc)
        self.save(update_fields=['subtotal', 'total'])


class VentaDetalle(models.Model):
    """Línea de detalle de una venta."""

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = 'Detalle de venta'
        verbose_name_plural = 'Detalles de venta'

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        self.venta.recalcular_totales()

    def delete(self, *args, **kwargs):
        venta = self.venta
        super().delete(*args, **kwargs)
        venta.recalcular_totales()
