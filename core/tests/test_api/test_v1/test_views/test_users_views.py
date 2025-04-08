from django.urls import reverse

from users.models import User

from unittest.mock import patch

from geant_examples.models import Example, ExampleCommand, UserExampleCommand

from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest

from api.v1.serializers.users_serializers import UserProfileSerializer

from rest_framework.exceptions import ErrorDetail


class UserProfileTestCase(AuthSettingsTest):
    def setUp(self):
        self.url = reverse('user-profile')

    def test_retrieve_user_ok(self):
        self.login_user()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, UserProfileSerializer(self.user).data)

    def test_not_loggined_in(self):
        response = self.client.get(self.url)

        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(
            response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_update_ok(self):
        self.login_user()
        new_data = {'first_name': 'new_fname'}
        response = self.client.patch(
            self.url, data=new_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.get(
            username=self.user.username).first_name, new_data['first_name'])

    def test_delete_user(self):
        self.login_user()

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(
            username=self.user.username).exists())

    def test_change_username(self):
        data = {
            'new_username': 'afs',
            'password': 'test_pas1'
        }
        self.login_user()

        response = self.client.post(
            reverse('user-profile-update-username'), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(
            username=self.user.username).exists())
        self.assertTrue(User.objects.filter(
            username=data['new_username']).exists())

    def test_username_already_exists(self):
        self.login_user()
        data = {
            'new_username': self.user.username,
            'password': 'test_pas1'
        }

        response = self.client.post(
            reverse('user-profile-update-username'), data=data)

        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.data, {'non_field_errors': [ErrorDetail(
            string='User with this username already exists', code='invalid')]})

    def test_change_username_wrong_pas(self):
        self.login_user()
        data = {
            'new_username': 'asad',
            'password': 'test_as1'
        }

        response = self.client.post(
            reverse('user-profile-update-username'), data=data)

        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.data, {'non_field_errors': [
                         ErrorDetail(string='Given wrong password', code='invalid')]})

    @patch('api.tasks.send_celery_mail.delay')
    def test_email_verify(self, mock_mail):
        self.login_user()
        self.user.is_email_verified = True
        self.user.save()
        url = reverse('user-profile-email-verify')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, {'error': 'Your email already verified'})

        self.user.is_email_verified = False
        self.user.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, {'detail': 'We sent mail on your email to email verify'})
        mock_mail.assert_called_once()


class UserExampleViewTestCase(AuthSettingsTest):
    def test_get_examples(self):
        ex_data = {
            "title_verbose": "test_verbose",
            'title_not_verbose': 'TSU_XX_00',
            "category": "default"
        }
        example = Example.objects.create(**ex_data)
        ex_command = ExampleCommand.objects.create(
            key_s3='key-s3-TSU_XX_00___v=11', example=example)
        ex_command.users.add(self.user)
        us_ex_command = UserExampleCommand.objects.get(user=self.user)

        self.login_user()
        response = self.client.get(reverse('user-examples'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, [{'title_verbose': ex_data['title_verbose'], 'description': '', 'creation_date': str(us_ex_command.creation_date)[:-6].replace(' ', 'T') + 'Z', 'date_to_update': example.date_to_update, 'status': 0, 'params': {'v': '11'}}])
