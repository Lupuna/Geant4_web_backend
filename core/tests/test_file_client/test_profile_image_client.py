import os
from io import BytesIO
from unittest import mock
from unittest.mock import Mock, patch
from django.test import TestCase
from django.conf import settings

from file_client.S3_client import S3FileLoader
from file_client.base_file_client import render_then_cleanup
from file_client.exceptions import FileClientException
from file_client.profile_image_client import ProfileImageRendererClient


class ProfileImageRendererClientTestCase(TestCase):
    def setUp(self):
        self.correct_name = 'fnuf.png'
        self.name = "fnuf.fnuf"
        self.path = os.path.join(settings.PATH_TO_LOCAL_STORAGE, 'gig.fnuf')
        self.client = ProfileImageRendererClient(name=self.name, path=self.path)
        self.client.loader = Mock(spec=S3FileLoader)
        self.client.loader.update = Mock()
        self.client.loader.upload = Mock()
        self.client.loader.download_stream = Mock()
        self.client.loader.download = Mock()
        self.client.loader.delete = Mock()

    def test_init_sets_correct_filename_and_path(self):
        expected_filename = f"{os.path.splitext(self.name)[0]}.{self.client.format}"
        expected_path = os.path.join(settings.PATH_TO_LOCAL_STORAGE, expected_filename)

        self.assertEqual(self.client.filename, expected_filename)
        self.assertEqual(self.client.new_path, expected_path)

    def test_upload_calls_render_and_upload(self):
        with patch.object(ProfileImageRendererClient, "render"):
            self.client.upload()

        self.client.loader.upload.assert_called_once()

    def test_update_calls_render_and_update(self):
        with patch.object(ProfileImageRendererClient, "render"):
            self.client.update()

        self.client.loader.update.assert_called_once()

    def test_download_stream_success(self):
        self.client.loader.download_stream.return_value = None
        self.client.is_read_only = True

        result = self.client.download_stream()
        self.assertEqual(result, self.path)
        self.client.loader.download_stream.assert_called_once_with(self.correct_name)

        self.client.is_read_only = False

    def test_download_stream_file_not_found(self):
        self.client.loader.download_stream.return_value = True
        self.client.is_read_only = True

        with self.assertRaises(FileClientException) as context:
            self.client.download_stream()

        self.client.is_read_only = False

    def test_download_success(self):
        expected_stream = BytesIO(b"test content")
        self.client.loader.download_temporary.return_value = expected_stream
        self.client.is_read_only = True

        result = self.client.download()
        self.assertIsInstance(result, BytesIO)
        self.assertEqual(result.getvalue(), b"test content")
        self.client.loader.download_temporary.assert_called_once_with(self.correct_name)

        self.client.is_read_only = False

    def test_download_file_not_found(self):
        self.client.loader.download_temporary.return_value = None
        self.client.is_read_only = True

        with self.assertRaises(FileClientException) as context:
            self.client.download()

        self.client.is_read_only = False

    def test_delete(self):
        self.client.loader.delete.return_value = "deleted"
        self.client.is_read_only = True

        result = self.client.delete()
        self.assertEqual(result, "deleted")

        self.client.is_read_only = False

    @patch("os.path.exists", return_value=False)
    @patch("os.remove")
    def test_cleanup_when_no_files_exist(self, mock_remove, mock_exists):
        self.client.cleanup()
        mock_remove.assert_not_called()

    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_cleanup_when_files_exist(self, mock_remove, mock_exists):
        self.client.cleanup()
        self.assertEqual(mock_remove.call_count, 2)

    @patch("file_client.profile_image_client.Image.open")
    def test_render_raises_file_not_found(self, mock_open):
        mock_open.side_effect = FileNotFoundError

        with self.assertRaises(FileNotFoundError):
            self.client.render()


class RenderThenCleanupDecoratorTestCase(TestCase):

    @mock.patch("logging.getLogger")
    def test_decorator_calls_render_and_cleanup(self, mock_logger):
        processor = FakeProcessor()
        processor.process()

        self.assertTrue(processor.render_called)
        self.assertTrue(processor.cleanup_called)

    @mock.patch("logging.getLogger")
    def test_decorator_without_exception(self, mock_logger):
        processor = FakeProcessor()
        result = processor.process()

        self.assertEqual(result, "processed")
        mock_logger.return_value.error.assert_not_called()


class FakeProcessor:
    def __init__(self):
        self.render_called = False
        self.cleanup_called = False

    def render(self):
        self.render_called = True

    def cleanup(self):
        self.cleanup_called = True

    @render_then_cleanup
    def process(self):
        return "processed"
