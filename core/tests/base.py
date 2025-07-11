from django.conf import settings
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.test import TestCase
from loguru import logger

from geant_documentation.models import File
from geant_documentation.signals import destroy_file
from geant_examples.models import Example, Command, ExampleCommand
from geant_examples.signals import (
    delete_example,
    delete_command,
    save_example,
    save_command, update_user_example_command_document
)


class Base(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logger.remove()

        settings.ELASTICSEARCH_DSL_AUTOSYNC = False
        post_save.disconnect(
            receiver=save_example,
            sender=Example
        )
        post_save.disconnect(
            receiver=save_command,
            sender=Command
        )
        post_delete.disconnect(
            receiver=delete_example,
            sender=Example
        )
        post_delete.disconnect(
            receiver=delete_command,
            sender=Command
        )

        post_delete.disconnect(
            receiver=destroy_file,
            sender=File
        )
        m2m_changed.disconnect(
            receiver=update_user_example_command_document,
            sender=ExampleCommand.users.through
        )

    @classmethod
    def tearDownClass(cls):
        post_save.connect(
            receiver=save_example,
            sender=Example
        )
        post_save.disconnect(
            receiver=save_command,
            sender=Command
        )
        post_delete.connect(
            receiver=delete_example,
            sender=Example
        )
        post_delete.connect(
            receiver=delete_command,
            sender=Command
        )
        post_delete.connect(
            receiver=destroy_file,
            sender=File
        )
        m2m_changed.connect(
            receiver=update_user_example_command_document,
            sender=ExampleCommand.users.through
        )
        settings.ELASTICSEARCH_DSL_AUTOSYNC = True

        super().tearDownClass()