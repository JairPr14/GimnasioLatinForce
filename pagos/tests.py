from django.test import TestCase
from django.utils import timezone

from clientes.models import Cliente
from pagos.forms import PagoForm
from pagos.models import Deuda
from planes.models import Plan


class PagoFormTests(TestCase):
    def setUp(self):
        fecha = timezone.localdate()
        self.cliente = Cliente.objects.create(
            nombres='Ana',
            apellidos='Lopez',
            dni='11111111',
            telefono='900000001',
            fecha_inscripcion=fecha,
        )
        self.otro_cliente = Cliente.objects.create(
            nombres='Luis',
            apellidos='Garcia',
            dni='22222222',
            telefono='900000002',
            fecha_inscripcion=fecha,
        )
        self.plan = Plan.objects.create(
            nombre='Mensual',
            tipo_periodo='mensual',
            duracion_dias=30,
            precio='90.00',
        )
        self.deuda = Deuda.objects.create(
            cliente=self.cliente,
            monto='50.00',
            descripcion='Saldo pendiente',
        )

    def test_rechaza_deuda_de_otro_cliente(self):
        form = PagoForm(data={
            'cliente': self.otro_cliente.pk,
            'plan': '',
            'deuda': self.deuda.pk,
            'monto': '20.00',
            'metodo_pago': 'efectivo',
            'fecha_pago': timezone.localdate().isoformat(),
            'concepto': 'Abono',
            'numero_comprobante': '',
            'observaciones': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('deuda', form.errors)

    def test_rechaza_abono_mayor_a_la_deuda_pendiente(self):
        form = PagoForm(data={
            'cliente': self.cliente.pk,
            'plan': '',
            'deuda': self.deuda.pk,
            'monto': '80.00',
            'metodo_pago': 'efectivo',
            'fecha_pago': timezone.localdate().isoformat(),
            'concepto': 'Abono',
            'numero_comprobante': '',
            'observaciones': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('monto', form.errors)

    def test_rechaza_mezclar_plan_y_deuda_en_un_mismo_pago(self):
        form = PagoForm(data={
            'cliente': self.cliente.pk,
            'plan': self.plan.pk,
            'deuda': self.deuda.pk,
            'monto': '20.00',
            'metodo_pago': 'efectivo',
            'fecha_pago': timezone.localdate().isoformat(),
            'concepto': 'Pago mixto',
            'numero_comprobante': '',
            'observaciones': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
