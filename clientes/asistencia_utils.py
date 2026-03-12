"""
Utilidades para el módulo de asistencia.
"""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from pagos.models import Pago
from inventario.models import Producto
from ventas.models import Venta, VentaDetalle

from .models import Asistencia, AsistenciaInvitado

MAX_ASISTENCIAS_POR_DIA = 2
MAX_INVITADOS_POR_MES = 3


def cliente_tiene_plan_activo(cliente):
    """True si el cliente tiene un plan vigente (no vencido)."""
    hoy = timezone.now().date()
    ultimo = Pago.objects.filter(
        cliente=cliente, plan__isnull=False
    ).select_related('plan').order_by('-fecha_pago').first()
    if not ultimo:
        return False
    vence = ultimo.fecha_pago + timedelta(days=ultimo.plan.duracion_dias)
    return hoy <= vence


def cliente_en_mora(cliente):
    """True si el cliente tuvo plan pero está vencido, anulado o en mora."""
    ultimo = Pago.objects.filter(
        cliente=cliente, plan__isnull=False
    ).select_related('plan').order_by('-fecha_pago').first()
    if not ultimo:
        return False
    hoy = timezone.now().date()
    vence = ultimo.fecha_pago + timedelta(days=ultimo.plan.duracion_dias)
    if ultimo.plan and not ultimo.plan.activo:
        return True
    return hoy > vence


def asistencias_hoy_count(cliente):
    """Cantidad de ingresos (asistencias) del cliente hoy."""
    hoy = timezone.now().date()
    return Asistencia.objects.filter(
        cliente=cliente,
        fecha_hora_ingreso__date=hoy
    ).count()


def puede_registrar_ingreso_hoy(cliente):
    """True si el cliente puede registrar otra asistencia hoy (máx 2 por día)."""
    return asistencias_hoy_count(cliente) < MAX_ASISTENCIAS_POR_DIA


def invitados_mes_count(cliente):
    """Cantidad de invitados que el cliente ha registrado en el mes actual."""
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    return AsistenciaInvitado.objects.filter(
        asistencia__cliente=cliente,
        fecha_registro__date__gte=inicio_mes,
    ).count()


def puede_traer_invitado(cliente):
    """True si el cliente tiene plan activo y no ha usado sus 3 invitados del mes."""
    if not cliente_tiene_plan_activo(cliente):
        return False
    return invitados_mes_count(cliente) < MAX_INVITADOS_POR_MES


def get_or_create_producto_rutina():
    """Obtiene o crea el producto 'Rutina' (S/ 5) para venta de entrada por rutina."""
    prod, _ = Producto.objects.get_or_create(
        codigo='RUTINA-001',
        defaults={
            'nombre': 'Entrada por rutina',
            'precio': Decimal('5.00'),
            'stock': 9999,
            'permitir_vender_sin_stock': True,
            'descripcion': 'Entrada única al gimnasio para cliente sin plan activo',
        }
    )
    return prod


def registrar_venta_rutina_y_asistencia(cliente, usuario):
    """
    Crea una venta de rutina (S/ 5) y registra la asistencia.
    Retorna (venta, asistencia) o None si falla.
    """
    producto = get_or_create_producto_rutina()
    hoy = timezone.now().date()
    ultimo = Venta.objects.filter(serie='BB01').order_by('-id').first()
    n = (ultimo.id + 1) if ultimo else 1

    venta = Venta.objects.create(
        cliente=cliente,
        fecha_emision=hoy,
        tipo_comprobante='boleta',
        serie='BB01',
        numero_comprobante=f"{n:06d}",
        estado='emitido',
        usuario=usuario,
        subtotal=Decimal('5.00'),
        total=Decimal('5.00'),
        observaciones='Entrada por rutina - cliente sin plan activo',
    )

    VentaDetalle.objects.create(
        venta=venta,
        producto=producto,
        cantidad=Decimal('1'),
        precio_unitario=Decimal('5.00'),
        subtotal=Decimal('5.00'),
    )

    asistencia = Asistencia.objects.create(
        cliente=cliente,
        fecha_hora_ingreso=timezone.now(),
    )
    return venta, asistencia
