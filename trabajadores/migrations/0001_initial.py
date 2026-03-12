from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Trabajador",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombres", models.CharField(max_length=100)),
                ("apellidos", models.CharField(max_length=100)),
                ("documento", models.CharField(blank=True, max_length=20)),
                ("telefono", models.CharField(blank=True, max_length=30)),
                ("correo", models.EmailField(blank=True, max_length=254)),
                ("direccion", models.TextField(blank=True)),
                ("cargo", models.CharField(blank=True, max_length=80)),
                ("sueldo_mensual", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("estado", models.CharField(choices=[("activo", "Activo"), ("inactivo", "Inactivo")], default="activo", max_length=20)),
                ("fecha_ingreso", models.DateField(blank=True, null=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Trabajador",
                "verbose_name_plural": "Trabajadores",
                "ordering": ["apellidos", "nombres"],
            },
        ),
        migrations.CreateModel(
            name="PagoTrabajador",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha_pago", models.DateField()),
                ("monto", models.DecimalField(decimal_places=2, max_digits=12)),
                ("metodo_pago", models.CharField(choices=[("efectivo", "Efectivo"), ("transferencia", "Transferencia"), ("yape", "Yape"), ("plin", "Plin"), ("tarjeta", "Tarjeta")], default="efectivo", max_length=20)),
                ("concepto", models.CharField(blank=True, max_length=200)),
                ("numero_comprobante", models.CharField(blank=True, max_length=50)),
                ("observaciones", models.TextField(blank=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("trabajador", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pagos", to="trabajadores.trabajador")),
                ("usuario_registro", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pagos_trabajadores_registrados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Pago a trabajador",
                "verbose_name_plural": "Pagos a trabajadores",
                "ordering": ["-fecha_pago", "-id"],
            },
        ),
    ]

