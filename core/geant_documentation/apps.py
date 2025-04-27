from django.apps import AppConfig


class GeantDocumentationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'geant_documentation'

    def ready(self):
        from . import signals