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

    path("<int:trabajador_id>/adelantos/", views.AdelantoTrabajadorListView.as_view(), name="adelanto_list"),
    path("<int:trabajador_id>/adelantos/nuevo/", views.AdelantoTrabajadorCreateView.as_view(), name="adelanto_create"),
    path("<int:trabajador_id>/adelantos/<int:pk>/eliminar/", views.AdelantoTrabajadorDeleteView.as_view(), name="adelanto_delete"),

    path("<int:trabajador_id>/descuentos/", views.DescuentoTrabajadorListView.as_view(), name="descuento_list"),
    path("<int:trabajador_id>/descuentos/nuevo/", views.DescuentoTrabajadorCreateView.as_view(), name="descuento_create"),
    path("<int:trabajador_id>/descuentos/<int:pk>/eliminar/", views.DescuentoTrabajadorDeleteView.as_view(), name="descuento_delete"),

    path("reportes/pagos/", views.ReportePagosTrabajadoresView.as_view(), name="reporte_pagos"),

    path("asistencia/", views.AsistenciaTrabajadorListView.as_view(), name="asistencia_list"),
    path("asistencia/rapido/", views.AsistenciaTrabajadorRegistroRapidoView.as_view(), name="asistencia_rapido"),
    path("<int:trabajador_id>/asistencia/", views.AsistenciaTrabajadorTrabajadorListView.as_view(), name="asistencia_trabajador_list"),
    path("asistencia/<int:pk>/editar/", views.AsistenciaTrabajadorUpdateView.as_view(), name="asistencia_edit"),
]

