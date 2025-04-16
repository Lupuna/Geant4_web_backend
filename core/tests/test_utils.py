import requests

from django.conf import settings
from unittest.mock import patch, MagicMock

from geant_examples.models import Example, Command
from utils import DatabaseSynchronizer
from tests.base import Base

class DatabaseSynchronizerTestCase(Base):
    def setUp(self):
        self.example = Example.objects.create(
            title_not_verbose="TSU_XX_00",
            title_verbose="test_example"
        )
        self.command1 = Command.objects.create(
            example=self.example,
            title="command1",
            order_index=1,
            default="default1"
        )
        self.command2 = Command.objects.create(
            example=self.example,
            title="command2",
            order_index=2,
            default="default2"
        )

    def test_init_with_example(self):
        sync = DatabaseSynchronizer(example=self.example)
        self.assertEqual(sync.example, self.example)
        self.assertEqual(len(sync.commands), 2)

    def test_init_with_command(self):
        mock_command = MagicMock()
        mock_command.example = self.example
        sync = DatabaseSynchronizer(command=mock_command)
        self.assertEqual(sync.example, self.example)
        self.assertEqual(len(sync.commands), 2)

    def test_prepare_commands(self):
        sync = DatabaseSynchronizer(example=self.example)
        commands_data = sync.prepare_commands()

        self.assertEqual(len(commands_data), 2)
        self.assertEqual(commands_data[0]["title"], "command1")
        self.assertEqual(commands_data[0]["order_index"], 1)
        self.assertEqual(commands_data[0]["default"], "default1")
        self.assertEqual(commands_data[1]["title"], "command2")
        self.assertEqual(commands_data[1]["order_index"], 2)
        self.assertEqual(commands_data[1]["default"], "default2")

    def test_prepare_data(self):
        sync = DatabaseSynchronizer(example=self.example)
        data = sync.prepare_data()

        self.assertEqual(data["title"], self.example.title_not_verbose)
        self.assertEqual(len(data["commands"]), 2)
        self.assertEqual(data["commands"][0]["title"], "command1")

    @patch('requests.get')
    def test_get_example_from_backend_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 123, "detail": "success"}
        mock_get.return_value = mock_response

        sync = DatabaseSynchronizer(example=self.example)
        example_id = sync.get_example_from_backend()

        self.assertEqual(example_id, 123)
        mock_get.assert_called_once_with(
            url=settings.GEANT_BACKEND_GET_EXAMPLE_URL.format(title=self.example.title_not_verbose)
        )

    @patch('requests.get')
    def test_get_example_from_backend_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"detail": "Example not found"}
        mock_get.return_value = mock_response

        sync = DatabaseSynchronizer(example=self.example)
        example_id = sync.get_example_from_backend()

        self.assertEqual(example_id, -1)

    @patch('requests.get')
    def test_get_example_from_backend_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        sync = DatabaseSynchronizer(example=self.example)

        with self.assertRaises(requests.exceptions.RequestException):
            sync.get_example_from_backend()

    @patch('utils.DatabaseSynchronizer.get_example_from_backend')
    @patch('requests.delete')
    def test_drop_example_success(self, mock_delete, mock_get_example):
        mock_get_example.return_value = 123
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        sync = DatabaseSynchronizer(example=self.example)
        sync.drop_example()

        mock_delete.assert_called_once_with(
            settings.GEANT_BACKEND_DELETE_EXAMPLE_URL.format(id=123)
        )

    @patch('utils.DatabaseSynchronizer.get_example_from_backend')
    @patch('requests.delete')
    def test_drop_example_not_found(self, mock_delete, mock_get_example):
        mock_get_example.return_value = -1

        sync = DatabaseSynchronizer(example=self.example)
        sync.drop_example()

        mock_delete.assert_not_called()

    @patch('utils.DatabaseSynchronizer.get_example_from_backend')
    @patch('requests.delete')
    def test_drop_example_error(self, mock_delete, mock_get_example):
        mock_get_example.return_value = 123
        mock_delete.side_effect = requests.exceptions.RequestException("API Error")

        sync = DatabaseSynchronizer(example=self.example)
        sync.drop_example()

        mock_delete.assert_called_once()

    @patch('requests.post')
    def test_create_example_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        sync = DatabaseSynchronizer(example=self.example)
        sync.create_example()

        expected_data = {
            "title": self.example.title_not_verbose,
            "commands": [
                {
                    "title": "command1",
                    "order_index": 1,
                    "default": "default1"
                },
                {
                    "title": "command2",
                    "order_index": 2,
                    "default": "default2"
                }
            ]
        }

        mock_post.assert_called_once_with(
            url=settings.GEANT_BACKEND_CREATE_EXAMPLE_URL,
            json=expected_data
        )

    @patch('requests.post')
    def test_create_example_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        sync = DatabaseSynchronizer(example=self.example)

        with self.assertRaises(requests.exceptions.RequestException):
            sync.create_example()

    @patch('utils.DatabaseSynchronizer.drop_example')
    @patch('utils.DatabaseSynchronizer.create_example')
    @patch('utils.DatabaseSynchronizer.get_example_from_backend')
    def test_run_example_exists(self, mock_get, mock_create, mock_drop):
        mock_get.return_value = 123

        sync = DatabaseSynchronizer(example=self.example)
        sync.run()

        mock_drop.assert_called_once_with(123)
        mock_create.assert_called_once()

    @patch('utils.DatabaseSynchronizer.create_example')
    @patch('utils.DatabaseSynchronizer.get_example_from_backend')
    def test_run_example_not_exists(self, mock_get, mock_create):
        mock_get.return_value = -1

        sync = DatabaseSynchronizer(example=self.example)
        sync.run()

        mock_create.assert_called_once()