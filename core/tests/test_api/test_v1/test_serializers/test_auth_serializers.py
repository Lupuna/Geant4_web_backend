from django.db.models import Model
from django.test import TestCase

from api.v1.serializers.auth_serializers import RegistrationSerializer

from users.models import User

from rest_framework.exceptions import ErrorDetail


class RegistrationSerializerTestCase(TestCase):
    def setUp(self):
        self.data = {
            "email": "user@example.com",
            "username": "test_username",
            "first_name": "test_f",
            "last_name": "test_l",
            "password": "test_pas",
            "password2": "test_pas"
        }

    def test_save_ok(self):
        self.assertFalse(User.objects.filter(
            username=self.data['username']).exists())

        serializer = RegistrationSerializer(data=self.data)

        if serializer.is_valid():
            serializer.save()

        self.assertTrue(User.objects.filter(
            username=self.data['username']).exists())

    def test_validate(self):
        data = self.data
        data.update({'password': 'sfasf'})
        serializer = RegistrationSerializer(data=data)
        serializer.is_valid()

        self.assertEqual(serializer.errors, {'non_field_errors': [
                         ErrorDetail(string='Passwords do not match', code='invalid')]})
