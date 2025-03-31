from django.urls import reverse

from geant_examples.models import Example, ExampleCommand, UserExampleCommand

from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest

from api.v1.serializers.examples_serializers import ExampleCommandPOSTSerializer

from unittest.mock import patch, MagicMock


class ExampleCommandViewSetTestCase(AuthSettingsTest):
    def setUp(self):
        self.example = Example.objects.create(
            title_verbose='test_verbose', title_not_verbose='TSU_MM_99')
        self.params = {
            'params': {
                'velocity': 144
            }
        }

    @patch('requests.post', autospec=True)
    def test_create_ok(self, mock_post):
        mock_storage_resp = MagicMock()
        mock_storage_resp.status_code = 400
        mock_geant_resp = MagicMock()
        mock_geant_resp.status_code = 200
        mock_post.side_effect = [mock_storage_resp, mock_geant_resp]

        self.assertFalse(ExampleCommand.objects.filter(
            example=self.example, key_s3='key-s3_velocity_144').exists())
        self.login_user()
        response = self.client.post(reverse(
            'example-example-command-list', kwargs={'example_pk': self.example.id}), data=self.params, content_type='application/json')
        self.assertTrue(ExampleCommand.objects.filter(
            example=self.example, key_s3='key-s3_velocity_144').exists())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {'params': 'key-s3_velocity_144'})

    @patch('requests.post')
    def test_create_file_already_exixst(self, mock_post):
        mock_stor_resp = MagicMock()
        mock_stor_resp.status_code = 200
        mock_stor_resp.headers = {
            'Content-Disposition': 'attachment; filename="key-s3_velocity_144.zip"'}
        mock_stor_resp.content = b'file data'
        mock_post.return_value = mock_stor_resp

        self.login_user()
        self.assertFalse(ExampleCommand.objects.filter(
            example=self.example, key_s3='key-s3_velocity_144').exists())

        response = self.client.post(reverse(
            'example-example-command-list', kwargs={'example_pk': self.example.id}), data=self.params, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(ExampleCommand.objects.filter(
            example=self.example, key_s3='key-s3_velocity_144').exists())
        self.assertEqual(b''.join(response.streaming_content), b'file data')

    @patch('requests.post')
    def test_create_example_executing(self, mock_storage_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_storage_post.return_value = mock_resp

        ex_command = ExampleCommand.objects.create(
            key_s3='key-s3_velocity_144', example=self.example)
        self.assertFalse(self.user in ex_command.users.all())

        self.login_user()
        response = self.client.post(reverse(
            'example-example-command-list', kwargs={'example_pk': self.example.id}), data=self.params, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {'error': 'Example already executed, wait for results'})
        self.assertTrue(self.user in ex_command.users.all())

    @patch('requests.post', autospec=True)
    def test_create_geant_failure(self, mock_post):
        mock_storage_resp = MagicMock()
        mock_storage_resp.status_code = 400
        mock_geant_resp = MagicMock()
        mock_geant_resp.status_code = 400
        mock_geant_resp.json.return_value = {"error": "smth error"}
        mock_post.side_effect = [mock_storage_resp, mock_geant_resp]

        self.login_user()
        response = self.client.post(reverse(
            'example-example-command-list', kwargs={'example_pk': self.example.id}), data=self.params, content_type='application/json')
        self.assertEqual(response.status_code, mock_geant_resp.status_code)
        self.assertEqual(response.data, {"error": "smth error"})


class ExampleCommandUpdateStatusAPIViewTestCAse(AuthSettingsTest):
    def setUp(self):
        self.example = Example.objects.create(
            title_verbose='test_verbose', title_not_verbose='TSU_MM_99')
        self.ex_command = ExampleCommand.objects.create(
            key_s3='key-s3_velocity_144', example=self.example)
        self.ex_command.users.add(self.user)
        self.us_ex_command = UserExampleCommand.objects.get(
            example_command=self.ex_command, user=self.user)

    def test_update_status_to_failure(self):
        data = {
            'key_s3': 'key-s3_velocity_144',
            'err_body': 'smth err'
        }
        self.assertEqual(self.us_ex_command.status, 0)
        response = self.client.post(
            reverse('update-example-status'), data=data)
        self.us_ex_command.refresh_from_db()
        self.assertEqual(self.us_ex_command.status, 2)

    def test_update_status_to_executed(self):
        data = {
            'key_s3': 'key-s3_velocity_144'
        }
        self.assertEqual(self.us_ex_command.status, 0)
        response = self.client.post(
            reverse('update-example-status'), data=data)
        self.us_ex_command.refresh_from_db()
        self.assertEqual(self.us_ex_command.status, 1)
