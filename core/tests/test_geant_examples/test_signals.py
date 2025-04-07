from unittest.mock import patch
from unittest import TestCase

from django.conf import settings
from geant_examples.models import Example


class SendRequestOnCreateSignalTests(TestCase):
    def setUp(self):
        settings.BACKEND_URL = 'http://somedomain.ru/'

    @patch('requests.post')
    def test_signal_sends_request_on_create(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 201

        instance = Example.objects.create(title_not_verbose="TSU_XX_00")
        mock_post.assert_called_once_with(
            settings.BACKEND_URL,
            json={'title': 'TSU_XX_00'},
            headers={'Content-Type': 'application/json'}
        )


    @patch('requests.post')
    def test_signal_does_nothing_on_update(self, mock_post):
        instance = Example.objects.create(title_not_verbose="TSU_XX_00")

        mock_post.reset_mock()

        instance.title_not_verbose = "TSU_XX_01"
        instance.save()

        mock_post.assert_not_called()
