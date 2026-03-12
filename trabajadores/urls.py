from django.urls import path

from . import views

app_name = "trabajadores"

urlpatterns = [
    path("", views.TrabajadorListView.as_view(), name="list"),
    path("nuevo/", views.TrabajadorCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", views.TrabajadorUpdateView.as_view(), name="update"),
    path("<int:pk>/eliminar/", views.TrabajadorDeleteView.as_view(), name="delete"),
    path("<int:pk>/", views.TrabajadorDetailView.as_view(), name="detail"),

    path("<int:trabajador_id>/pagos/", views.PagoTrabajadorListView.as_view(), name="pago_list"),
    path("<int:trabajador_id>/pagos/nuevo/", views.PagoTrabajadorCreateView.as_view(), name="pago_create"),
    path("<int:trabajador_id>/pagos/<int:pk>/editar/", views.PagoTrabajadorUpdateView.as_view(), name="pago_update"),
    path("<int:trabajador_id>/pagos/<int:pk>/comprobante/", views.PagoTrabajadorComprobanteView.as_view(), name="pago_comprobante"),
    path("<int:trabajador_id>/pagos/<int:pk>/pdf/", views.pago_trabajador_comprobante_pdf, name="pago_comprobante_pdf"),

    path("<int:trabajador_id>/sueldos/", views.SueldoHistorialListView.as_view(), name="sueldo_list"),
    path("<int:trabajador_id>/sueldos/nuevo/", views.SueldoHistorialCreateView.as_view(), name="sueldo_create"),

    path("reportes/pagos/", views.ReportePagosTrabajadoresView.as_view(), name="reporte_pagos"),
]

