from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'precio', 'stock', 'unidad', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'codigo', 'codigo_barras')
