from django.test import TestCase
from django.db.models.signals import post_save, post_delete
from unittest.mock import patch, MagicMock

from geant_examples.models import Example, Command
from geant_examples.signals import (
    delete_example,
    save_example
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
