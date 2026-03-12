from django.db import models


class ConfiguracionEmpresa(models.Model):
    """Configuración única de la empresa (logo, etc.). Singleton."""
    logo = models.ImageField(
        upload_to='config/logo/',
        blank=True,
        null=True,
        verbose_name='Logo de la empresa'
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración empresa'
        verbose_name_plural = 'Configuración empresa'

    def __str__(self):
        return 'Configuración'

    @classmethod
    def obtener(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={})
        return obj
