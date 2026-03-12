"""
URLs de la app core.
"""
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'core'

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),
    path('configuracion/', views.ConfiguracionEmpresaView.as_view(), name='configuracion_empresa'),
]
