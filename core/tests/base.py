from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.test import TestCase
from loguru import logger

from geant_examples.models import Command, Example
from geant_examples.signals import (
    delete_example,
    delete_command,
    save_command
)


class Base(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logger.remove()

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
        settings.ELASTICSEARCH_DSL_AUTOSYNC = True

        super().tearDownClass()