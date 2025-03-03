from api.v1.serializers.users_serializers import LoginUpdateSerializer, PasswordUpdateSerializer

from users.models import User

from django.test import TestCase


class UsersSerializersSetUpClass(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test_email1@gmail.com',
            username='test_username1',
            first_name='test_fname1',
            last_name='test_lname1'
        )
        self.user.set_password('test_pas1')
        self.user.save()


class LoginUpdateSerializerTestCase(UsersSerializersSetUpClass):
    def test_validate(self):
        data = {
            'new_username': 'pasos',
            'password': 'test_pas1'
        }

        serializer = LoginUpdateSerializer(instance=self.user, data=data)
        self.assertTrue(serializer.is_valid())

        data.update({'new_username': self.user.username})
        serializer = LoginUpdateSerializer(instance=self.user, data=data)
        self.assertFalse(serializer.is_valid())

        data.update({'new_username': 'pasos', 'password': 'ds'})
        serializer = LoginUpdateSerializer(instance=self.user, data=data)
        self.assertFalse(serializer.is_valid())

    def test_update(self):
        data = {
            'new_username': 'pasos',
            'password': 'test_pas1'
        }
        serializer = LoginUpdateSerializer(instance=self.user, data=data)

        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertTrue(User.objects.filter(
            username=data['new_username']).exists())
        self.assertFalse(User.objects.filter(
            username='test_username1').exists())


class PasswordUpdateSerializerTestCase(UsersSerializersSetUpClass):
    def test_validate(self):
        data = {
            'new_password': 'assalamu_alaikum',
            'new_password2': 'assalamu_alaikum'
        }

        serializer = PasswordUpdateSerializer(instance=self.user, data=data)
        self.assertTrue(serializer.is_valid())

        data.update({'new_password': 'gygy'})
        serializer = PasswordUpdateSerializer(instance=self.user, data=data)
        self.assertFalse(serializer.is_valid())

    def test_update(self):
        data = {
            'new_password': 'assalamu_alaikum',
            'new_password2': 'assalamu_alaikum'
        }
        serializer = PasswordUpdateSerializer(instance=self.user, data=data)

        self.assertTrue(User.objects.get(
            username=self.user.username).check_password('test_pas1'))
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertTrue(User.objects.get(
            username=self.user.username).check_password(data['new_password']))
