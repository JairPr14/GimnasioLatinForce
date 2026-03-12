"""
URLs principales del proyecto LatinForce.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('core.urls', 'core'), namespace='core')),
    path('', include('usuarios.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('clientes/', include('clientes.urls')),
    path('planes/', include('planes.urls')),
    path('pagos/', include('pagos.urls')),
    path('inventario/', include('inventario.urls')),
    path('ventas/', include('ventas.urls')),
    path('trabajadores/', include('trabajadores.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
