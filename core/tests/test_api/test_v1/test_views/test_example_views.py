from unittest.mock import patch, MagicMock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from api.v1.views.examples_views import ExampleCommandViewSet
from geant_examples.models import Example, ExampleCommand, UserExampleCommand
from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest

from file_client.files_clients import ReadOnlyClient
from file_client.exceptions import FileClientException


class ExampleCommandViewSetTestCase(AuthSettingsTest):
    def setUp(self):
        self.example = Example.objects.create(
            title_verbose='test_verbose', title_not_verbose='TSU_99'
        )
        self.params = {'params': {'velocity': '144'}}
        self.key_s3 = 'key-s3-TSU_99___velocity=144'
        self.factory = APIRequestFactory()
        self.url = reverse('example-example-command-list',
                           kwargs={'example_pk': self.example.id})
        self.view = ExampleCommandViewSet()

    def test_generate_key_s3(self):
        str_params = {
            str(k).replace(' ', '---'): str(v).replace(' ', '---')
            for k, v in self.params['params'].items()
        }
        correct_meaning = f'key-s3-{self.example.title_not_verbose}___' + \
            '___'.join(f'{k}={v}' for k, v in str_params.items())
        self.assertEqual(correct_meaning,
                         ExampleCommandViewSet._generate_key_s3(self.example.title_not_verbose, self.params['params']))

    def test_add_user_in_example_command(self):
        ExampleCommandViewSet._add_user_in_example_command(
            self.example, self.key_s3, self.user)

        ex_command = ExampleCommand.objects.get(
            key_s3=self.key_s3, example=self.example)
        self.assertIn(self.user, ex_command.users.all())

    def test_add_user_in_example_command_when_user_already_added(self):
        ex_command = ExampleCommand.objects.create(
            key_s3=self.key_s3, example=self.example)
        ex_command.users.add(self.user)

        ExampleCommandViewSet._add_user_in_example_command(
            self.example, self.key_s3, self.user)

        ex_command.refresh_from_db()
        self.assertEqual(ex_command.users.count(), 1)

    def test_example_executed(self):
        ex_command = ExampleCommand.objects.create(
            key_s3='some-key',
            example=self.example
        )
        ex_command.users.add(self.user)

        request = self.factory.post(
            self.url, self.params, format='json', example_pk=self.example.id)
        force_authenticate(request, user=self.user)

        self.view.setup(request=request, example_pk=self.example.id)
        ex_commands = self.view.get_queryset().prefetch_related(
            'example', 'users').filter(key_s3='some-key')
        response = ExampleCommandViewSet()._example_is_executing(ex_commands, self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ex_command.refresh_from_db()
        self.assertIn(self.user, ex_command.users.all())
        self.assertEqual(
            response.data, {'detail': 'Example already executed, wait for results'})

    def test_example_executed_when_user_already_added(self):
        ex_command = ExampleCommand.objects.create(
            key_s3='some-key',
            example=self.example
        )
        ex_command.users.add(self.user)

        request = self.factory.post(
            self.url, self.params, format='json', example_pk=self.example.id)
        force_authenticate(request, user=self.user)

        self.view.setup(request=request, example_pk=self.example.id)
        ex_commands = self.view.get_queryset().prefetch_related(
            'example', 'users').filter(key_s3='some-key')
        initial_user_count = ex_command.users.count()

        response = ExampleCommandViewSet()._example_is_executing(ex_commands, self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ex_command.refresh_from_db()
        self.assertEqual(ex_command.users.count(), initial_user_count)

        self.assertEqual(
            response.data, {'detail': 'Example already executed, wait for results'})

    @patch('api.v1.views.examples_views.requests.post')
    def test_run_example_failure(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=400,
            json=lambda: {'error': 'Bad request'},
            headers={'Content-Type': 'application/json'}
        )

        request = self.factory.post(self.url, self.params, format='json')
        force_authenticate(request, user=self.user)

        self.view.setup(request=request, kwargs={
                        'example_pk': self.example.id})

        response = self.view._run_example(
            request, self.example, self.params['params'])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'Bad request'})
        mock_post.assert_called_once()

    @patch('api.v1.views.examples_views.ReadOnlyClient')
    def test_run_failed_example(self, mock_post):
        mock_instance = mock_post.return_value
        mock_instance.download.side_effect = FileClientException(
            error='any', status=400)
        ex_command = ExampleCommand.objects.create(
            example=self.example, key_s3=self.key_s3)
        ex_command.users.add(self.user)
        update_status_data = {
            "key_s3": self.key_s3,
            "err_body": "string"
        }
        update_to_failure = self.client.post(path=reverse(
            'update-example-status'), data=update_status_data)
        self.assertEqual(update_to_failure.status_code, 204)
        self.assertEqual(UserExampleCommand.objects.get(
            user=self.user, example_command=ex_command).status, 2)
        self.login_user()
        response = self.client.post(
            self.url, data=self.params, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {'detail': 'Example executing was finished in error'})


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
