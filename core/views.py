"""
Vistas del módulo core.
"""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from usuarios.permissions import RolePermissionRequiredMixin
from .forms import ConfiguracionEmpresaForm
from .models import ConfiguracionEmpresa


class ConfiguracionEmpresaView(RolePermissionRequiredMixin, View):
    """Vista para editar configuración de la empresa (logo)."""
    required_perms = ["seguridad.usuarios"]

    def get(self, request):
        config = ConfiguracionEmpresa.obtener()
        form = ConfiguracionEmpresaForm(instance=config)
        return render(request, 'core/configuracion_empresa.html', {'form': form, 'config': config})

    def post(self, request):
        config = ConfiguracionEmpresa.obtener()
        form = ConfiguracionEmpresaForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración guardada correctamente.')
            return redirect('core:configuracion_empresa')
        return render(request, 'core/configuracion_empresa.html', {'form': form, 'config': config})
