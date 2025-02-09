from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from users.models import User

from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest

from api.v1.serializers.users_serializers import UserProfileSerializer


class UserProfileViewSetTestCase(AuthSettingsTest):
    def setUp(self):
        self.url = reverse('user-profile-detail', kwargs={'pk': self.user.id})

    def login_user(self):
        self.client.post(reverse('login'), data={
                         'username': self.user.username, 'password': 'test_pas1'})

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
        new_data = {'username': 'new_username'}
        response = self.client.patch(
            self.url, data=new_data, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, UserProfileSerializer(
            User.objects.get(username=new_data['username'])).data)

    def test_delete_user(self):
        self.login_user()

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(username=self.user.username).exists())
