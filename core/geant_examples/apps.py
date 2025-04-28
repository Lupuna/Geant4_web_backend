from django.apps import AppConfig


class GeantExamplesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'geant_examples'

    def ready(self):
        from . import signals
