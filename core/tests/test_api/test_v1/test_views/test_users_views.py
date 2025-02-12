from django.urls import reverse

from users.models import User

from geant_examples.models import Example

from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest

from api.v1.serializers.users_serializers import UserProfileSerializer


class UserProfileViewSetTestCase(AuthSettingsTest):
    def setUp(self):
        self.url = reverse('user-profile-detail', kwargs={'pk': self.user.id})

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
