import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente
from inventario.models import Producto
from ventas.models import Venta


class VentaCreateViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='caja',
            email='caja@example.com',
            password='secret123',
        )
        self.cliente = Cliente.objects.create(
            nombres='Mario',
            apellidos='Rojas',
            dni='33333333',
            telefono='900000003',
            fecha_inscripcion=timezone.localdate(),
        )
        self.producto = Producto.objects.create(
            nombre='Proteina',
            codigo='PRD-9001',
            precio='15.00',
            stock=5,
        )
        self.client.force_login(self.user)

    def _payload(self, items):
        return {
            'cliente': self.cliente.pk,
            'fecha_emision': timezone.localdate().isoformat(),
            'fecha_vencimiento': '',
            'tipo_comprobante': 'boleta',
            'serie': 'BB01',
            'tipo_operacion': 'venta_interna',
            'descuento_global': '10',
            'es_proforma': '',
            'observaciones': '',
            'condicion_pago': '',
            'items_json': json.dumps(items),
        }

    def test_no_crea_venta_sin_items(self):
        with patch('ventas.views.VentaCreateView.form_invalid', return_value=HttpResponseBadRequest('invalid')):
            response = self.client.post(reverse('ventas:create'), self._payload([]))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Venta.objects.count(), 0)

    def test_crea_venta_valida_y_descuenta_stock(self):
        response = self.client.post(reverse('ventas:create'), self._payload([
            {
                'producto_id': self.producto.pk,
                'cantidad': 2,
                'precio': '15.00',
            }
        ]))

        self.assertEqual(response.status_code, 302)
        venta = Venta.objects.get()
        self.producto.refresh_from_db()

        self.assertEqual(venta.detalles.count(), 1)
        self.assertEqual(venta.subtotal, Decimal('30.00'))
        self.assertEqual(venta.total, Decimal('27.00'))
        self.assertEqual(self.producto.stock, 3)
