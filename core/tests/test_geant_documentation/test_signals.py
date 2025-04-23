from unittest.mock import patch

from django.test import TestCase

from geant_documentation.models import File, Article, Subscription, Element


class FileSignalTestCase(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title='test_title',
            description='test_description',
        )
        self.subscription = Subscription.objects.create(
            title='test_title',
            subscription_order=1,
            article=self.article
        )
        self.element = Element.objects.create(
            text="Old",
            element_order=1,
            type="image",
            subscription=self.subscription
        )

    def test_destroy_file_webp_triggers_correct_task(self):
        file = File.objects.create(format='webp', element=self.element)
        file_uuid = str(file.uuid)

        with patch('geant_documentation.signals.destroy_documentation_image_task.delay') as mock_task:
            file.delete()
            mock_task.assert_called_once_with(name=file_uuid)

    def test_destroy_file_csv_triggers_correct_task(self):
        file = File.objects.create(format='csv', element=self.element)
        file_uuid = str(file.uuid)

        with patch('geant_documentation.signals.destroy_documentation_graphic_task.delay') as mock_task:
            file.delete()
            mock_task.assert_called_once_with(name=file_uuid)
