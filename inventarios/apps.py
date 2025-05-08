from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InventariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventarios'
    verbose_name = _('Inventarios')

    def ready(self):
        # Importar señales
        import inventarios.signals
