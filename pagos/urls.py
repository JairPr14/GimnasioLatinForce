"""
URLs del módulo Pagos.
"""
from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
    path('', views.PagoListView.as_view(), name='list'),
    path('nuevo/', views.PagoCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.PagoUpdateView.as_view(), name='update'),
    path('<int:pk>/comprobante/', views.PagoComprobanteView.as_view(), name='comprobante'),
    path('<int:pk>/pdf/', views.pago_comprobante_pdf, name='comprobante_pdf'),
    path('historial/<int:cliente_id>/', views.PagoHistorialClienteView.as_view(), name='historial_cliente'),
    path('deudas/', views.DeudaListView.as_view(), name='deuda_list'),
    path('deudas/nueva/', views.DeudaCreateView.as_view(), name='deuda_create'),
    path('reportes/', views.ReporteIngresosView.as_view(), name='reportes'),
]
