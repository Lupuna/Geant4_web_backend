from django.apps import AppConfig
from django.db.models.signals import post_migrate


class GeantTestsStorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'geant_tests_storage'

    def ready(self):
        from geant_tests_storage.signals import create_default_groups, set_file_mode
        post_migrate.connect(create_default_groups, sender=self)
        post_migrate.connect(set_file_mode, sender=self)
