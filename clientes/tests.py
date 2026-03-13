from datetime import datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone

from clientes.asistencia_utils import registrar_venta_rutina_y_asistencia
from clientes.models import Asistencia, Cliente
from clientes.views import AsistenciaRegistrarView
from pagos.models import Pago
from planes.models import Plan
from ventas.models import Venta


class AsistenciaTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='secret123',
        )
        self.cliente = Cliente.objects.create(
            nombres='Juan',
            apellidos='Perez',
            dni='12345678',
            telefono='999999999',
            fecha_inscripcion=timezone.localdate(),
        )

    def _build_request(self, data):
        request = self.factory.post(reverse('clientes:asistencia_registrar'), data)
        request.user = self.user
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        setattr(request, '_messages', FallbackStorage(request))
        return request

    def test_rutina_no_se_registra_si_ya_tiene_ingreso_abierto(self):
        Asistencia.objects.create(
            cliente=self.cliente,
            fecha_hora_ingreso=timezone.now() - timedelta(minutes=30),
        )

        with self.assertRaisesMessage(ValueError, 'ya tiene un ingreso abierto'):
            registrar_venta_rutina_y_asistencia(self.cliente, self.user)

        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(Asistencia.objects.filter(cliente=self.cliente).count(), 1)

    def test_rutina_no_se_registra_si_tiene_plan_activo(self):
        plan = Plan.objects.create(
            nombre='Mensual',
            tipo_periodo='mensual',
            duracion_dias=30,
            precio='80.00',
        )
        Pago.objects.create(
            cliente=self.cliente,
            plan=plan,
            monto=plan.precio,
            metodo_pago='efectivo',
            fecha_pago=timezone.localdate(),
            concepto='Mensual',
            usuario_registro=self.user,
        )

        with self.assertRaisesMessage(ValueError, 'ya tiene un plan activo'):
            registrar_venta_rutina_y_asistencia(self.cliente, self.user)

        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(Asistencia.objects.filter(cliente=self.cliente).count(), 0)

    def test_registro_manual_respeta_limite_diario(self):
        plan = Plan.objects.create(
            nombre='Mensual',
            tipo_periodo='mensual',
            duracion_dias=30,
            precio='80.00',
        )
        Pago.objects.create(
            cliente=self.cliente,
            plan=plan,
            monto=plan.precio,
            metodo_pago='efectivo',
            fecha_pago=timezone.localdate(),
            concepto='Mensual',
            usuario_registro=self.user,
        )
        hoy = timezone.localdate()
        primer_ingreso = timezone.make_aware(datetime.combine(hoy, time(hour=8)))
        segundo_ingreso = timezone.make_aware(datetime.combine(hoy, time(hour=10)))
        Asistencia.objects.create(
            cliente=self.cliente,
            fecha_hora_ingreso=primer_ingreso,
            fecha_hora_egreso=primer_ingreso + timedelta(hours=1),
        )
        Asistencia.objects.create(
            cliente=self.cliente,
            fecha_hora_ingreso=segundo_ingreso,
            fecha_hora_egreso=segundo_ingreso + timedelta(hours=1),
        )

        request = self._build_request({'dni': self.cliente.dni, 'accion': 'registrar_ingreso'})
        with patch('clientes.views.render', return_value=HttpResponse('ok')):
            response = AsistenciaRegistrarView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Asistencia.objects.filter(cliente=self.cliente).count(), 2)
