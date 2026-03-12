"""
Vistas del módulo Planes.
"""
from django.contrib import messages
from usuarios.permissions import RolePermissionRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import PlanForm
from .models import Plan


class PlanListView(RolePermissionRequiredMixin, ListView):
    """Listado de planes con búsqueda."""
    model = Plan
    template_name = 'planes/plan_list.html'
    context_object_name = 'planes'
    paginate_by = 15
    required_perms = ["planes.view"]

    def get_queryset(self):
        qs = Plan.objects.all()
        q = self.request.GET.get('q', '').strip()
        tipo = self.request.GET.get('tipo', '')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion_promocion__icontains=q))
        if tipo:
            qs = qs.filter(tipo_periodo=tipo)
        return qs


class PlanDetailView(RolePermissionRequiredMixin, DetailView):
    """Detalle del plan."""
    model = Plan
    template_name = 'planes/plan_detail.html'
    context_object_name = 'plan'
    required_perms = ["planes.view"]


class PlanCreateView(RolePermissionRequiredMixin, CreateView):
    """Crear nuevo plan."""
    model = Plan
    form_class = PlanForm
    template_name = 'planes/plan_form.html'
    success_url = reverse_lazy('planes:list')
    required_perms = ["planes.create"]

    def form_valid(self, form):
        messages.success(self.request, 'Plan creado correctamente.')
        return super().form_valid(form)


class PlanUpdateView(RolePermissionRequiredMixin, UpdateView):
    """Editar plan."""
    model = Plan
    form_class = PlanForm
    template_name = 'planes/plan_form.html'
    context_object_name = 'plan'
    success_url = reverse_lazy('planes:list')
    required_perms = ["planes.update"]

    def form_valid(self, form):
        messages.success(self.request, 'Plan actualizado correctamente.')
        return super().form_valid(form)


class PlanDeleteView(RolePermissionRequiredMixin, DeleteView):
    """Eliminar plan."""
    model = Plan
    template_name = 'planes/plan_confirm_delete.html'
    context_object_name = 'plan'
    success_url = reverse_lazy('planes:list')
    required_perms = ["planes.delete"]

    def form_valid(self, form):
        messages.success(self.request, 'Plan eliminado correctamente.')
        return super().form_valid(form)
