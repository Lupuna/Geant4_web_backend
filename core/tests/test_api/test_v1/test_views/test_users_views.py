from django.urls import reverse

from users.models import User

from geant_examples.models import Example

from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest

from api.v1.serializers.users_serializers import UserProfileSerializer

from rest_framework.exceptions import ErrorDetail


class UserProfileViewSetTestCase(AuthSettingsTest):
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

    def test_get_examples(self):
        ex_data = {
            "title": "haha",
            "key_s3": "asxxzx",
            "category": "default"
        }
        example = Example.objects.create(**ex_data)
        example.users.add(self.user)

        self.login_user()
        response = self.client.get(reverse('user-profile-user-examples'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, [{'title': 'haha', 'tags': [], 'status': 2}])

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

    def test_change_pas(self):
        self.login_user()
        data = {
            'new_password': 'sdklfas',
            'new_password2': 'sdklfas'
        }

        response = self.client.post(
            reverse('user-profile-update-password'), data=data)

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=self.user.username)
        self.assertFalse(user.check_password('test_pas1'))
        self.assertTrue(user.check_password(data['new_password']))
