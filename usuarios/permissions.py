from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class AdminOrRoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Permite acceso a superusers o usuarios con rol "admin" (código).
    """

    required_role_code = "admin"

    def test_func(self) -> bool:
        u = self.request.user
        if not u.is_authenticated:
            return False
        if getattr(u, "is_superuser", False):
            return True
        return u.roles_asignados.filter(rol__codigo=self.required_role_code, rol__activo=True).exists()


def user_has_perm(user, perm_code: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.roles_asignados.filter(
        rol__activo=True,
        rol__permisos__codigo=perm_code,
    ).exists()


class RolePermissionRequiredMixin(LoginRequiredMixin):
    """
    Requiere 1+ permisos (códigos) para acceder.
    - Superuser siempre pasa.
    - Si required_perms está vacío, solo requiere login.
    """

    required_perms: list[str] = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not self.required_perms:
            return super().dispatch(request, *args, **kwargs)
        if getattr(request.user, "is_superuser", False):
            return super().dispatch(request, *args, **kwargs)
        ok = any(user_has_perm(request.user, p) for p in self.required_perms)
        if not ok:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

