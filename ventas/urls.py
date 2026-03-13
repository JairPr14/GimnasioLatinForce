from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.VentaListView.as_view(), name='list'),
    path('reporte/', views.ReporteVentasView.as_view(), name='reporte'),
    path('nueva/', views.VentaCreateView.as_view(), name='create'),
    path('<int:pk>/', views.VentaDetailView.as_view(), name='detail'),
    path('<int:pk>/comprobante/', views.VentaComprobanteView.as_view(), name='comprobante'),
    path('<int:pk>/pdf/', views.venta_comprobante_pdf, name='comprobante_pdf'),
]
