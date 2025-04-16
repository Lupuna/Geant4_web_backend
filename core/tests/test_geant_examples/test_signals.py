from django.test import TestCase
from django.db.models.signals import post_save, post_delete
from unittest.mock import patch, MagicMock

from geant_examples.models import Example, Command
from geant_examples.signals import (
    delete_example,
    delete_command,
    save_command
)

class ExampleSignalTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.data = {
            "title_not_verbose": "TSU_XX_00",
            "title_verbose": "test_verbose_title"
        }
        post_delete.connect(
            receiver=delete_example,
            sender=Example
        )

    def tearDown(self):
        post_delete.disconnect(
            receiver=delete_example,
            sender=Example
        )

        super().tearDown()

    @patch("geant_examples.signals.DatabaseSynchronizer")
    def test_post_delete(self, mock_sync):
        mock_sync_obj = MagicMock()
        mock_sync.return_value = mock_sync_obj

        example = Example.objects.create(**self.data)
        example.delete()

        mock_sync.assert_called_once_with(example=example)
        mock_sync_obj.drop_example.assert_called_once()

class CommandSignalTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.example = Example.objects.create(
            title_not_verbose="TSU_XX_00",
            title_verbose="test_verbose_title"
        )
        self.data = {
            "title": "test_title",
            "order_index": 1,
            "default": "test_default",
            "example": self.example
        }

        post_delete.connect(
            receiver=delete_command,
            sender=Command
        )
        post_save.connect(
            receiver=save_command,
            sender=Command
        )

    def tearDown(self):
        post_delete.disconnect(
            receiver=delete_command,
            sender=Command
        )
        post_save.disconnect(
            receiver=save_command,
            sender=Command
        )

        super().tearDown()

    @patch("geant_examples.signals.DatabaseSynchronizer")
    def test_post_delete(self, mock_sync):
        mock_sync_obj = MagicMock()
        mock_sync.return_value = mock_sync_obj

        command = Command.objects.create(**self.data)

        mock_sync.reset_mock()

        command.delete()

        mock_sync.assert_called_once_with(command=command)
        mock_sync_obj.run.assert_called_once()

    @patch("geant_examples.signals.DatabaseSynchronizer")
    def test_post_save(self, mock_sync):
        mock_sync_obj = MagicMock()
        mock_sync.return_value = mock_sync_obj

        command = Command.objects.create(**self.data)

        mock_sync.assert_called_once_with(command=command)
        mock_sync_obj.run.assert_called_once()