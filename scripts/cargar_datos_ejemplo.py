"""
Script para cargar datos de ejemplo: 5 clientes, 5 promociones, 5 productos.
Ejecutar: python scripts/cargar_datos_ejemplo.py
"""
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.utils import timezone

from clientes.models import Cliente
from planes.models import Plan
from inventario.models import Producto
from pagos.models import Pago, Deuda
from clientes.asistencia_utils import get_or_create_producto_rutina
from trabajadores.models import Trabajador


def cargar_clientes():
    datos = [
        {'nombres': 'María', 'apellidos': 'García López', 'dni': '12345678A', 'telefono': '5551234001',
         'correo': 'maria.garcia@email.com', 'direccion': 'Calle Principal 1', 'fecha_inscripcion': date(2025, 1, 15),
         'fecha_nacimiento': date(1995, 3, 10)},
        {'nombres': 'Carlos', 'apellidos': 'Rodríguez Sánchez', 'dni': '23456789B', 'telefono': '5551234002',
         'correo': 'carlos.rodriguez@email.com', 'direccion': 'Av. Central 45', 'fecha_inscripcion': date(2025, 2, 1),
         'fecha_nacimiento': date(1990, 7, 22)},
        {'nombres': 'Ana', 'apellidos': 'Martínez Ruiz', 'dni': '34567890C', 'telefono': '5551234003',
         'correo': 'ana.martinez@email.com', 'direccion': 'Calle Secundaria 78', 'fecha_inscripcion': date(2025, 2, 10),
         'fecha_nacimiento': date(1998, 11, 5)},
        {'nombres': 'Luis', 'apellidos': 'Hernández Torres', 'dni': '45678901D', 'telefono': '5551234004',
         'correo': 'luis.hernandez@email.com', 'direccion': 'Jardines del Norte 12', 'fecha_inscripcion': date(2025, 3, 1),
         'fecha_nacimiento': date(1988, 4, 18)},
        {'nombres': 'Laura', 'apellidos': 'Díaz Mendoza', 'dni': '56789012E', 'telefono': '5551234005',
         'correo': 'laura.diaz@email.com', 'direccion': 'Colonia Sur 56', 'fecha_inscripcion': date(2025, 3, 8),
         'fecha_nacimiento': date(1992, 9, 30)},
    ]
    for d in datos:
        obj, created = Cliente.objects.get_or_create(dni=d['dni'], defaults=d)
        print(f"  {'Creado' if created else 'Ya existe'}: {obj}")
    return len(datos)


def cargar_promociones():
    datos = [
        {'nombre': 'Promo Verano 2x1', 'tipo_periodo': 'mensual', 'duracion_dias': 60,
         'precio': Decimal('599.00'), 'es_promocion': True,
         'descripcion_promocion': 'Paga 1 mes y lleva 2. Válido hasta fin de temporada.'},
        {'nombre': 'Año Nuevo - 20% OFF', 'tipo_periodo': 'anual', 'duracion_dias': 365,
         'precio': Decimal('4799.00'), 'es_promocion': True,
         'descripcion_promocion': 'Plan anual con 20% de descuento. Incluye acceso ilimitado.'},
        {'nombre': 'Primera Vez 50% OFF', 'tipo_periodo': 'mensual', 'duracion_dias': 30,
         'precio': Decimal('299.50'), 'es_promocion': True,
         'descripcion_promocion': 'Solo para nuevos miembros. Primer mes a mitad de precio.'},
        {'nombre': 'Promo Semanal Express', 'tipo_periodo': 'semanal', 'duracion_dias': 14,
         'precio': Decimal('149.00'), 'es_promocion': True,
         'descripcion_promocion': '2 semanas por el precio de 1. Prueba el gimnasio.'},
        {'nombre': 'Plan Parejas', 'tipo_periodo': 'mensual', 'duracion_dias': 30,
         'precio': Decimal('899.00'), 'es_promocion': True,
         'descripcion_promocion': 'Inscríbete con un amigo o pareja. Dos membresías mensuales.'},
    ]
    for d in datos:
        obj, created = Plan.objects.get_or_create(nombre=d['nombre'], es_promocion=True, defaults=d)
        print(f"  {'Creado' if created else 'Ya existe'}: {obj}")
    return len(datos)


def cargar_productos():
    datos = [
        {'nombre': 'Proteína Whey 1kg', 'codigo': 'SUP-001', 'precio': Decimal('599.00'), 'stock': 25,
         'descripcion': 'Proteína de suero de leche, sabor vainilla.'},
        {'nombre': 'Creatina Monohidrato 300g', 'codigo': 'SUP-002', 'precio': Decimal('349.00'), 'stock': 40,
         'descripcion': 'Creatina pura para rendimiento deportivo.'},
        {'nombre': 'Bebida isotónica 500ml', 'codigo': 'BEV-001', 'precio': Decimal('35.00'), 'stock': 120,
         'descripcion': 'Bebida deportiva para hidratación.'},
        {'nombre': 'Camiseta LatinForce', 'codigo': 'MER-001', 'precio': Decimal('249.00'), 'stock': 50,
         'descripcion': 'Camiseta oficial del gimnasio.'},
        {'nombre': 'Pre-entrenamiento 300g', 'codigo': 'SUP-003', 'precio': Decimal('449.00'), 'stock': 18,
         'descripcion': 'Energía y enfoque para entrenamientos intensos.'},
    ]
    for d in datos:
        obj, created = Producto.objects.get_or_create(codigo=d['codigo'], defaults=d)
        print(f"  {'Creado' if created else 'Ya existe'}: {obj}")
    return len(datos)


def cargar_trabajadores():
    datos = [
        {'nombres': 'Roberto', 'apellidos': 'Flores Vega', 'documento': '87654321', 'telefono': '5559876001',
         'correo': 'roberto.flores@latinforce.com', 'direccion': 'Av. Los Deportistas 100', 'cargo': 'Entrenador',
         'sueldo_mensual': Decimal('1800.00'), 'fecha_ingreso': date(2024, 1, 15)},
        {'nombres': 'Sandra', 'apellidos': 'Quispe Mamani', 'documento': '76543210', 'telefono': '5559876002',
         'correo': 'sandra.quispe@latinforce.com', 'direccion': 'Calle del Gym 45', 'cargo': 'Recepcionista',
         'sueldo_mensual': Decimal('1200.00'), 'fecha_ingreso': date(2024, 3, 1)},
        {'nombres': 'Miguel', 'apellidos': 'Castro Rojas', 'documento': '65432109', 'telefono': '5559876003',
         'correo': 'miguel.castro@latinforce.com', 'direccion': 'Jr. Atletas 22', 'cargo': 'Entrenador',
         'sueldo_mensual': Decimal('1900.00'), 'fecha_ingreso': date(2024, 5, 10)},
        {'nombres': 'Patricia', 'apellidos': 'Torres Silva', 'documento': '54321098', 'telefono': '5559876004',
         'correo': 'patricia.torres@latinforce.com', 'direccion': 'Colonia Fitness 78', 'cargo': 'Nutricionista',
         'sueldo_mensual': Decimal('1500.00'), 'fecha_ingreso': date(2024, 7, 20)},
        {'nombres': 'Jorge', 'apellidos': 'Mendoza López', 'documento': '43210987', 'telefono': '5559876005',
         'correo': 'jorge.mendoza@latinforce.com', 'direccion': 'Av. Principal 150', 'cargo': 'Mantenimiento',
         'sueldo_mensual': Decimal('950.00'), 'fecha_ingreso': date(2024, 9, 1)},
    ]
    for d in datos:
        obj, created = Trabajador.objects.get_or_create(documento=d['documento'], defaults=d)
        print(f"  {'Creado' if created else 'Ya existe'}: {obj}")
    return len(datos)


def cargar_rutina():
    """Asegura que exista el producto Rutina (S/ 5) para entrada por rutina."""
    prod = get_or_create_producto_rutina()
    print(f"  Producto: {prod.nombre} (S/ {prod.precio})")
    return 1


def cargar_clientes_prueba():
    """5 clientes de prueba: distintos planes, días mora, deudas pendientes."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    usuario = User.objects.first()

    hoy = timezone.now().date()

    # Asegurar que un plan tenga días de gracia (mora)
    plan_mensual, _ = Plan.objects.get_or_create(
        nombre='Plan Mensual Básico', es_promocion=False,
        defaults={'tipo_periodo': 'mensual', 'duracion_dias': 30, 'precio': Decimal('399.00'),
                  'dias_gracia_mora': 5}
    )
    if plan_mensual.dias_gracia_mora == 0:
        plan_mensual.dias_gracia_mora = 5
        plan_mensual.save()
        print("  Plan Mensual Básico: actualizado dias_gracia_mora=5")

    planes = list(Plan.objects.filter(activo=True))
    promo_verano = Plan.objects.filter(nombre__icontains='Verano').first()
    promo_semanal = Plan.objects.filter(nombre__icontains='Semanal').first()
    plan_anual = Plan.objects.filter(nombre__icontains='Año Nuevo').first()
    primera_vez = Plan.objects.filter(nombre__icontains='Primera Vez').first()

    clientes_datos = [
        # 1. Ricardo: plan activo (Promo Verano), pago reciente
        {'nombres': 'Ricardo', 'apellidos': 'Vega Campos', 'dni': '11111111', 'telefono': '5551111001',
         'correo': 'ricardo.vega@test.com', 'direccion': 'Calle Prueba 1', 'fecha_inscripcion': date(2025, 2, 1),
         'fecha_nacimiento': date(1993, 5, 15),
         'pagos': [{'plan': promo_verano or planes[0], 'fecha': hoy - timedelta(days=10), 'concepto': 'Promo Verano 2x1'}]},
        # 2. Fernanda: en mora (plan venció hace 20 días)
        {'nombres': 'Fernanda', 'apellidos': 'Salas Montes', 'dni': '22222222', 'telefono': '5552222002',
         'correo': 'fernanda.salas@test.com', 'direccion': 'Av. Prueba 22', 'fecha_inscripcion': date(2025, 1, 10),
         'fecha_nacimiento': date(1996, 8, 20),
         'pagos': [{'plan': primera_vez or planes[0], 'fecha': hoy - timedelta(days=55), 'concepto': 'Primera Vez 50%'}]},
        # 3. Pedro: tiene deuda pendiente S/ 300
        {'nombres': 'Pedro', 'apellidos': 'Ríos Delgado', 'dni': '33333333', 'telefono': '5553333003',
         'correo': 'pedro.rios@test.com', 'direccion': 'Jr. Prueba 33', 'fecha_inscripcion': date(2025, 2, 15),
         'fecha_nacimiento': date(1989, 12, 3),
         'pagos': [{'plan': plan_mensual or planes[0], 'fecha': hoy - timedelta(days=5), 'concepto': 'Plan Mensual'}],
         'deudas': [{'monto': Decimal('300.00'), 'descripcion': 'Saldo pendiente renovación anterior'}]},
        # 4. Carmen: plan semanal, vence en 3 días (próximo a vencer)
        {'nombres': 'Carmen', 'apellidos': 'Paredes Soto', 'dni': '44444444', 'telefono': '5554444004',
         'correo': 'carmen.paredes@test.com', 'direccion': 'Colonia Prueba 44', 'fecha_inscripcion': date(2025, 3, 1),
         'fecha_nacimiento': date(2000, 2, 14),
         'pagos': [{'plan': promo_semanal or planes[0], 'fecha': hoy - timedelta(days=11), 'concepto': 'Promo Semanal Express'}]},
        # 5. Andrés: en mora + deuda pendiente
        {'nombres': 'Andrés', 'apellidos': 'Maldonado Rojas', 'dni': '55555555', 'telefono': '5555555005',
         'correo': 'andres.maldonado@test.com', 'direccion': 'Urbanización Prueba 55', 'fecha_inscripcion': date(2024, 11, 1),
         'fecha_nacimiento': date(1991, 6, 8),
         'pagos': [{'plan': plan_anual or planes[0], 'fecha': hoy - timedelta(days=400), 'concepto': 'Año Nuevo 20% OFF'}]},
    ]
    # Ajustar cliente 5 con deuda
    clientes_datos[4]['deudas'] = [{'monto': Decimal('150.00'), 'descripcion': 'Mora por renovación'}, {'monto': Decimal('449.00'), 'descripcion': 'Plan Primera Vez pendiente'}]

    for datos in clientes_datos:
        pagos_data = datos.pop('pagos')
        deudas_data = datos.pop('deudas', [])

        cliente, created = Cliente.objects.get_or_create(dni=datos['dni'], defaults=datos)
        print(f"  {'Creado' if created else 'Ya existe'}: {cliente}")

        if created:
            for p in pagos_data:
                plan = p['plan']
                Pago.objects.create(
                    cliente=cliente, plan=plan, fecha_pago=p['fecha'], concepto=p['concepto'],
                    monto=plan.precio, metodo_pago='efectivo', usuario_registro=usuario,
                    numero_comprobante=f'PAG-TEST-{cliente.dni}-{p["fecha"]}'
                )
            for d in deudas_data:
                Deuda.objects.create(
                    cliente=cliente, descripcion=d['descripcion'], monto=d['monto'],
                    fecha_vencimiento=hoy + timedelta(days=15)
                )

    print("  Escenarios: plan activo, en mora, deuda pendiente, vence pronto, mora+deuda")
    return 5


def main():
    print("Cargando datos de ejemplo...")
    print("\n0. Producto Rutina (entrada sin plan):")
    cargar_rutina()
    print("\n1. Clientes (pacientes):")
    cargar_clientes()
    print("\n2. Promociones:")
    cargar_promociones()
    print("\n3. Productos (inventario):")
    cargar_productos()
    print("\n4. Trabajadores:")
    cargar_trabajadores()
    print("\n5. Clientes de prueba (planes, mora, deudas):")
    cargar_clientes_prueba()
    print("\n¡Listo! Datos cargados correctamente.")


if __name__ == '__main__':
    main()
