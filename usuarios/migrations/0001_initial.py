from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Rol",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=60, unique=True)),
                ("codigo", models.SlugField(help_text="Ej: admin, caja", max_length=40, unique=True)),
                ("descripcion", models.CharField(blank=True, max_length=160)),
                ("activo", models.BooleanField(default=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Rol",
                "verbose_name_plural": "Roles",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="UsuarioRol",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha_asignacion", models.DateTimeField(auto_now_add=True)),
                ("rol", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="usuarios_asignados", to="usuarios.rol")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="roles_asignados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Rol de usuario",
                "verbose_name_plural": "Roles de usuario",
                "unique_together": {("usuario", "rol")},
            },
        ),
    ]

