from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RolPermiso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(db_index=True, max_length=80)),
                ("fecha_asignacion", models.DateTimeField(auto_now_add=True)),
                ("rol", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="permisos", to="usuarios.rol")),
            ],
            options={
                "verbose_name": "Permiso de rol",
                "verbose_name_plural": "Permisos de rol",
                "ordering": ["codigo"],
                "unique_together": {("rol", "codigo")},
            },
        ),
    ]

