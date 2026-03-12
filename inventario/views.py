import re
from django.contrib import messages
from usuarios.permissions import RolePermissionRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.views import View

from .forms import ProductoForm
from .models import Producto


class ProductoListView(RolePermissionRequiredMixin, ListView):
    model = Producto
    template_name = 'inventario/producto_list.html'
    context_object_name = 'productos'
    paginate_by = 20
    required_perms = ["inventario.view"]

    def get_queryset(self):
        qs = Producto.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(codigo__icontains=q) |
                Q(codigo_barras__icontains=q)
            )
        return qs


class ProductoCreateView(RolePermissionRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'inventario/producto_form.html'
    success_url = reverse_lazy('inventario:list')
    required_perms = ["inventario.create"]

    def form_valid(self, form):
        if not (form.instance.codigo or '').strip():
            # Formato: PRD-0001 (4 dígitos), correlativo.
            ultimo = Producto.objects.order_by('-id').first()
            siguiente = (ultimo.id + 1) if ultimo else 1
            # En caso de huecos/borrados o concurrencia, reintentar hasta encontrar libre.
            while True:
                candidato = f"PRD-{siguiente:04d}"
                if not Producto.objects.filter(codigo=candidato).exists():
                    form.instance.codigo = candidato
                    break
                siguiente += 1
        messages.success(self.request, 'Producto registrado correctamente.')
        return super().form_valid(form)


class ProductoUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'inventario/producto_form.html'
    context_object_name = 'producto'
    success_url = reverse_lazy('inventario:list')
    required_perms = ["inventario.update"]

    def form_valid(self, form):
        messages.success(self.request, 'Producto actualizado correctamente.')
        return super().form_valid(form)


class ProductoDeleteView(RolePermissionRequiredMixin, DeleteView):
    model = Producto
    success_url = reverse_lazy('inventario:list')
    template_name = 'inventario/producto_confirm_delete.html'
    context_object_name = 'producto'
    required_perms = ["inventario.delete"]

    def form_valid(self, form):
        messages.success(self.request, 'Producto eliminado.')
        return super().form_valid(form)


class ProductoBuscarApiView(RolePermissionRequiredMixin, View):
    """API para buscar productos por nombre, código o código de barras (ventas)."""
    required_perms = ["ventas.create", "inventario.view"]
    def get(self, request):
        q = (request.GET.get('q') or '').strip()
        if not q:
            return JsonResponse({'productos': []})
        qs = Producto.objects.filter(activo=True).filter(
            Q(nombre__icontains=q) |
            Q(codigo__iexact=q) |
            Q(codigo_barras__iexact=q)
        )[:20]
        productos = [
            {
                'id': p.id,
                'nombre': p.nombre,
                'codigo': p.codigo,
                'precio': str(p.precio),
                'stock': p.stock,
                'unidad': p.unidad,
                'permitir_vender_sin_stock': p.permitir_vender_sin_stock,
            }
            for p in qs
        ]
        return JsonResponse({'productos': productos})
