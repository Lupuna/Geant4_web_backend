import os

from django.test import TestCase
from django.conf import settings

from unittest.mock import patch, MagicMock, mock_open

from core.storage import BackupStorage

class BackupStorageTestCase(TestCase):
    @patch("requests.post")
    def test_init_method(self, mock_post):
        storage = BackupStorage()

        mock_post.assert_called_once_with(
            url=settings.STORAGE_URL + "/upload/",
            files={"file": ("web-backend-backup.bin", b"")}
        )
        mock_post.return_value.raise_for_status.assert_called_once()

    @patch("requests.post")
    def test_init_backup(self, mock_post):
        storage = BackupStorage()

        mock_post.reset_mock()

        storage.init_backup()

        mock_post.assert_called_once_with(
            url=settings.STORAGE_URL + "/upload/",
            files={"file": ("web-backend-backup.bin", b"")}
        )
        mock_post.return_value.raise_for_status.assert_called_once()

    @patch("core.storage.TemporaryDirectory")
    @patch("requests.post")
    @patch("builtins.open", new_callable=mock_open)
    def test_open_method(self, mock_file, mock_post, mock_dir):
        mock_post.return_value.content = b""
        mock_temp_dir = "/mock/temp/dir"
        mock_dir.return_value.__enter__.return_value = mock_temp_dir

        storage = BackupStorage()

        mock_post.reset_mock()

        storage._open("web-backend-backup.bin", 'rb')

        mock_post.assert_called_once_with(

            url=settings.STORAGE_URL + "/retrieve/",
            json={
                "filename": "web-backend-backup.bin"
            }
        )
        path = os.path.join(mock_temp_dir, "web-backend-backup.bin")

        self.assertEqual(
            len(mock_file.call_args_list), 2
        )
        self.assertEqual(
            mock_file.call_args_list, [
                ((path, 'wb'),), ((path, "rb"),)
            ]
        )
        mock_file().write.assert_called_once_with(b"")

    @patch("requests.post")
    def test_save_method(self, mock_post):
        mock_content = MagicMock()
        mock_file = MagicMock()

        mock_content.open.return_value = mock_file

        storage = BackupStorage()

        mock_post.reset_mock()

        storage._save("web-backend-backup.bin", mock_content)


        mock_post.assert_called_once_with(
            url=settings.STORAGE_URL + "/update/",
            files={
                "file": ("web-backend-backup.bin", mock_file)
            }
        )
        mock_post.return_value.raise_for_status.assert_called_once()

        self.assertEqual(
            mock_content.open.call_args.kwargs, {"mode": "rb"}
        )



