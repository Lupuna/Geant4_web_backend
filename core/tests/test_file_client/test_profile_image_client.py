import os
from unittest import mock
from unittest.mock import Mock

from PIL import Image
from django.test import TestCase
from django.conf import settings

from file_client.S3_client import S3FileLoader
from file_client.base_file_client import render_then_cleanup
from file_client.profile_image_client import ProfileImageRendererClient


class ProfileImageRendererClientTestCase(TestCase):

    def setUp(self):
        self.client = ProfileImageRendererClient(os.path.join(settings.PATH_TO_LOCAL_STORAGE, 'gig.fnuf'), 'fnuf.fnuf')
        self.client.loader = Mock(spec=S3FileLoader)
        self.client.loader.update = Mock()
        self.client.loader.upload = Mock()

    def test_init(self):
        correct_filename = f"{os.path.splitext('fnuf.fnuf')[0]}.{self.client.format}"
        correct_filepath = os.path.join(settings.PATH_TO_LOCAL_STORAGE, correct_filename)
        self.assertEqual(self.client.new_filename, correct_filename)
        self.assertEqual(self.client.new_path, correct_filepath)

    def test_upload(self):
        with mock.patch("file_client.profile_image_client.ProfileImageRendererClient.render"):
            self.client.upload()

        self.client.loader.upload.assert_called_once()

    def test_update(self):
        with mock.patch("file_client.profile_image_client.ProfileImageRendererClient.render"):
            self.client.update()

        self.client.loader.update.assert_called_once()

    @mock.patch("os.path.exists")
    @mock.patch("os.remove")
    def test_cleanup_no_files_to_remove(self, mock_remove, mock_exists):
        mock_exists.side_effect = lambda path: False
        self.client.cleanup()
        mock_remove.assert_not_called()

    @mock.patch("os.path.exists")
    @mock.patch("os.remove")
    def test_cleanup_files_to_remove(self, mock_remove, mock_exists):
        mock_exists.side_effect = lambda path: True
        self.client.cleanup()
        mock_remove.assert_called()

    @mock.patch("file_client.profile_image_client.Image.open")
    @mock.patch("file_client.profile_image_client.Image.Image.save")
    def test_render_file_not_found(self, mock_save, mock_open):
        mock_open.side_effect = FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            self.client.render()

        mock_save.assert_not_called()


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
