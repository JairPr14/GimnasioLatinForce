"""
Modelos del módulo Inventario.
"""
from django.db import models
from django.db.models import Max


class Producto(models.Model):
    """Producto del inventario (suplementos, bebidas, merchandising, etc.)."""

    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')
    codigo_barras = models.CharField(max_length=100, blank=True, verbose_name='Código de barras')
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0, help_text='Cantidad en almacén')
    unidad = models.CharField(max_length=20, default='UND', help_text='UND, KG, L, etc.')
    activo = models.BooleanField(default=True)
    permitir_vender_sin_stock = models.BooleanField(
        default=False,
        verbose_name='Permitir vender sin stock',
        help_text='Si está activo, el producto puede venderse aunque el stock no alcance.'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def save(self, *args, **kwargs):
        # Autogenerar código si no viene (ej. PRD-0001).
        if not (self.codigo or '').strip():
            # Buscar el mayor correlativo ya usado para evitar duplicados
            pref = 'PRD-'
            max_num = 0
            for c in Producto.objects.filter(codigo__startswith=pref).values_list('codigo', flat=True):
                try:
                    max_num = max(max_num, int(c.replace(pref, '')))
                except (ValueError, TypeError):
                    continue
            self.codigo = f"{pref}{max_num + 1:04d}"
        super().save(*args, **kwargs)

    @property
    def stock_disponible(self):
        return max(0, self.stock)
