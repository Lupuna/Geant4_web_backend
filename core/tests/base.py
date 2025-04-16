from django.test import TestCase
from django.conf import settings
from django.db.models.signals import post_save, post_delete

from geant_examples.signals import (
    delete_example,
    delete_command,
    save_command
)
from geant_examples.models import Command, Example

class Base(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.ELASTICSEARCH_DSL_AUTOSYNC = False

        post_save.disconnect(
            receiver=save_command,
            sender=Command
        )
        post_delete.disconnect(
            receiver=delete_command,
            sender=Command
        )
        post_delete.disconnect(
            receiver=delete_example,
            sender=Example
        )

    @classmethod
    def tearDownClass(cls):
        post_save.connect(
            receiver=save_command,
            sender=Command
        )
        post_delete.connect(
            receiver=delete_command,
            sender=Command
        )
        post_delete.connect(
            receiver=delete_example,
            sender=Example
        )
        super().tearDownClass()