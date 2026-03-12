from django.conf import settings
from django.db import models


class Rol(models.Model):
    """
    Rol simple para control de acceso (UI).
    Ej: admin, caja, supervisor, etc.
    """

    nombre = models.CharField(max_length=60, unique=True)
    codigo = models.SlugField(max_length=40, unique=True, help_text="Ej: admin, caja")
    descripcion = models.CharField(max_length=160, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        return self.nombre


class UsuarioRol(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roles_asignados")
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name="usuarios_asignados")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rol de usuario"
        verbose_name_plural = "Roles de usuario"
        unique_together = (("usuario", "rol"),)

    def __str__(self) -> str:
        return f"{self.usuario} -> {self.rol}"


class RolPermiso(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name="permisos")
    codigo = models.CharField(max_length=80, db_index=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Permiso de rol"
        verbose_name_plural = "Permisos de rol"
        unique_together = (("rol", "codigo"),)
        ordering = ["codigo"]

    def __str__(self) -> str:
        return f"{self.rol.codigo}:{self.codigo}"
