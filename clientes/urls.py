"""
URLs del módulo Clientes.
"""
from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.ClienteListView.as_view(), name='list'),
    path('nuevo/', views.ClienteCreateView.as_view(), name='create'),
    path('asistencia/', views.AsistenciaRegistrarView.as_view(), name='asistencia_registrar'),
    path('asistencia/rapido/', views.AsistenciaRegistroRapidoView.as_view(), name='asistencia_rapido'),
    path('<int:pk>/', views.ClienteDetailView.as_view(), name='detail'),
    path('<int:pk>/asistencia/', views.AsistenciaClienteListView.as_view(), name='asistencia_list'),
    path('<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.ClienteDeleteView.as_view(), name='delete'),
]
