"""
URLs de la app core.
Redirige la raíz al dashboard (o login si no está autenticado).
"""
from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),
]
