"""
Vistas de autenticación personalizadas con mensajes.
"""
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import RolForm, UsuarioCreateForm, UsuarioUpdateForm
from .models import Rol
from .permissions import AdminOrRoleRequiredMixin, RolePermissionRequiredMixin

User = get_user_model()


class LoginView(auth_views.LoginView):
    """Login con mensaje de éxito."""

    def form_valid(self, form):
        messages.success(self.request, '¡Bienvenido! Has iniciado sesión correctamente.')
        return super().form_valid(form)


class LogoutView(auth_views.LogoutView):
    """Logout con mensaje de éxito."""

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, 'Has cerrado sesión correctamente.')
        return super().dispatch(request, *args, **kwargs)


# ----------- Usuarios (CRUD) -----------
class UsuarioListView(RolePermissionRequiredMixin, ListView):
    model = User
    template_name = "usuarios/usuario_list.html"
    context_object_name = "usuarios"
    paginate_by = 20
    required_perms = ["seguridad.usuarios"]

    def get_queryset(self):
        qs = User.objects.all().order_by("username")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(username__icontains=q)
        return qs


class UsuarioCreateView(RolePermissionRequiredMixin, CreateView):
    model = User
    form_class = UsuarioCreateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:usuario_list")
    required_perms = ["seguridad.usuarios"]

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado correctamente.")
        return super().form_valid(form)


class UsuarioUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = User
    form_class = UsuarioUpdateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:usuario_list")
    required_perms = ["seguridad.usuarios"]

    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado correctamente.")
        return super().form_valid(form)


class UsuarioDeleteView(RolePermissionRequiredMixin, DeleteView):
    model = User
    template_name = "usuarios/usuario_confirm_delete.html"
    success_url = reverse_lazy("usuarios:usuario_list")
    required_perms = ["seguridad.usuarios"]

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Usuario eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


# ----------- Roles (CRUD) -----------
class RolListView(RolePermissionRequiredMixin, ListView):
    model = Rol
    template_name = "usuarios/rol_list.html"
    context_object_name = "roles"
    paginate_by = 30
    required_perms = ["seguridad.roles"]


class RolCreateView(RolePermissionRequiredMixin, CreateView):
    model = Rol
    form_class = RolForm
    template_name = "usuarios/rol_form.html"
    success_url = reverse_lazy("usuarios:rol_list")
    required_perms = ["seguridad.roles"]

    def form_valid(self, form):
        messages.success(self.request, "Rol creado correctamente.")
        return super().form_valid(form)


class RolUpdateView(RolePermissionRequiredMixin, UpdateView):
    model = Rol
    form_class = RolForm
    template_name = "usuarios/rol_form.html"
    success_url = reverse_lazy("usuarios:rol_list")
    required_perms = ["seguridad.roles"]

    def form_valid(self, form):
        messages.success(self.request, "Rol actualizado correctamente.")
        return super().form_valid(form)


class RolDeleteView(RolePermissionRequiredMixin, DeleteView):
    model = Rol
    template_name = "usuarios/rol_confirm_delete.html"
    success_url = reverse_lazy("usuarios:rol_list")
    required_perms = ["seguridad.roles"]

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Rol eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
