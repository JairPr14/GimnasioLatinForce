"""
Vistas del módulo Clientes.
"""
from django.contrib import messages
from usuarios.permissions import RolePermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ClienteForm
from .models import Cliente


class ClienteListView(RolePermissionRequiredMixin, ListView):
    """Listado de clientes con búsqueda."""
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 15
    required_perms = ["clientes.view"]

    def get_queryset(self):
        qs = Cliente.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nombres__icontains=q) |
                Q(apellidos__icontains=q) |
                Q(dni__icontains=q)
            )
        return qs


class ClienteDetailView(RolePermissionRequiredMixin, DetailView):
    """Detalle del cliente."""
    model = Cliente
    template_name = 'clientes/cliente_detail.html'
    context_object_name = 'cliente'
    required_perms = ["clientes.view"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from datetime import timedelta
        from django.utils import timezone
        from pagos.models import Pago
        hoy = timezone.now().date()
        ultimo_pago = Pago.objects.filter(cliente=self.object, plan__isnull=False).select_related('plan').order_by('-fecha_pago').first()
        if ultimo_pago:
            fecha_vencimiento = ultimo_pago.fecha_pago + timedelta(days=ultimo_pago.plan.duracion_dias)
            ctx['ultimo_plan'] = ultimo_pago
            ctx['fecha_vencimiento_plan'] = fecha_vencimiento
            ctx['plan_activo'] = hoy <= fecha_vencimiento
        else:
            ctx['ultimo_plan'] = None
        return ctx


class ClienteCreateView(RolePermissionRequiredMixin, CreateView):
    """Crear nuevo cliente."""
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:list')
    required_perms = ["clientes.create"]

    def get_initial(self):
        from django.utils import timezone
        initial = super().get_initial()
        initial['fecha_inscripcion'] = timezone.now().date()
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Cliente registrado correctamente.')
        return super().form_valid(form)


class ClienteUpdateView(RolePermissionRequiredMixin, UpdateView):
    """Editar cliente."""
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    context_object_name = 'cliente'
    success_url = reverse_lazy('clientes:list')
    required_perms = ["clientes.update"]

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado correctamente.')
        return super().form_valid(form)


class ClienteDeleteView(RolePermissionRequiredMixin, DeleteView):
    """Eliminar cliente."""
    model = Cliente
    template_name = 'clientes/cliente_confirm_delete.html'
    context_object_name = 'cliente'
    success_url = reverse_lazy('clientes:list')
    required_perms = ["clientes.delete"]

    def form_valid(self, form):
        messages.success(self.request, 'Cliente eliminado correctamente.')
        return super().form_valid(form)
