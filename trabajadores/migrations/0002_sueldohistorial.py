from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("trabajadores", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SueldoHistorial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha_inicio", models.DateField()),
                ("sueldo_mensual", models.DecimalField(decimal_places=2, max_digits=12)),
                ("motivo", models.CharField(blank=True, max_length=160)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("trabajador", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sueldos", to="trabajadores.trabajador")),
                ("usuario_registro", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sueldos_trabajadores_registrados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Historial de sueldo",
                "verbose_name_plural": "Historial de sueldos",
                "ordering": ["-fecha_inicio", "-id"],
            },
        ),
    ]

