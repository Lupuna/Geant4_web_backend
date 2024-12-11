from django.test import TestCase

from django.contrib.auth import get_user_model


class UserManagerTestCase(TestCase):

    def setUp(self):
        self.user_model = get_user_model()
        self.valid_email = 'test_user@gmial.com'
        self.valid_password = 'test_password_123'
        self.valid_username = 'username'

    def test_create_user_with_email_success(self):
        user = self.user_model.objects.create_user(
            email=self.valid_email,
            password=self.valid_password,
            username=self.valid_username,
        )
        self.assertEqual(user.email, self.valid_email)
        self.assertTrue(user.check_password(self.valid_password))

    def tset_create_user_raises_error(self):
        with self.assertRaises(ValueError):
            self.user_model.objects.create_user(email=None, password=self.valid_password)

    def test_create_superuser(self):
        user = self.user_model.objects.create_user(
            email=self.valid_email,
            password=self.valid_password,
            username=self.valid_username,
        )
        self.assertEqual(user.email, self.valid_email)
        self.assertTrue(user.check_password(self.valid_password))
        self.assertFalse(user.is_staff)
