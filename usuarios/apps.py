from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    name = 'usuarios'

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver

        from .role_options import PERMISOS

        @receiver(post_migrate, sender=self)
        def ensure_admin_role_perms(sender, **kwargs):
            # Asigna todos los permisos definidos al rol "admin" por defecto
            from .models import Rol, RolPermiso

            rol, _ = Rol.objects.get_or_create(
                codigo="admin",
                defaults={"nombre": "Administrador", "descripcion": "Acceso total al panel", "activo": True},
            )
            existing = set(rol.permisos.values_list("codigo", flat=True))
            all_codes = {p.code for p in PERMISOS}
            to_add = list(all_codes - existing)
            if to_add:
                RolPermiso.objects.bulk_create([RolPermiso(rol=rol, codigo=c) for c in to_add], ignore_conflicts=True)
