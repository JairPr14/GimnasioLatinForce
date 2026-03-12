"""
Context processors para templates.
"""
def configuracion_empresa(request):
    """Inyecta la configuración de la empresa en todos los templates."""
    try:
        from .models import ConfiguracionEmpresa
        config = ConfiguracionEmpresa.obtener()
    except Exception:
        config = None
    return {'config_empresa': config}
