from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.exceptions import ErrorDetail

from freezegun import freeze_time

from unittest.mock import patch, MagicMock

from users.models import User

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest


class RegistrationAPIViewTestCase(AuthSettingsTest):
    def setUp(self):
        self.registration_data = {
            'username': 'test_username',
            'email': 'test_email@gmail.com',
            'first_name': 'test_first_name',
            'last_name': 'test_last_name',
            'password': 'test_password',
            'password2': 'test_password'
        }
        self.url = reverse('registration')

    @patch('api.tasks.send_celery_mail.delay')
    def test_registration_ok(self, mock_send):
        response = self.client.post(self.url, data=self.registration_data)

        self.assertTrue(User.objects.filter(
            username=self.registration_data['username']).exists())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.get(
            username=self.registration_data['username']).is_active)
        mock_send.assert_called_once()

    @patch('api.tasks.send_celery_mail.delay')
    def test_registration_bad(self, mock_send):
        data = self.registration_data
        data.update({'username': ''})

        response = self.client.post(self.url, data)

        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email=data['email']).exists())
        self.assertFalse(response.cookies.keys())
        mock_send.assert_not_called()

    @patch('api.tasks.send_celery_mail.delay')
    def test_registration_already_exists(self, mock_send):
        data = self.registration_data
        data.update({'username': self.user.username})

        response = self.client.post(self.url, data=data)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.data, {'username': [ErrorDetail(
            string='This value is already taken.', code='invalid')]})
        mock_send.assert_not_called()

    @patch('api.tasks.send_celery_mail.delay')
    def test_registration_second_time(self, mock_send):
        self.assertFalse(User.objects.filter(
            email=self.registration_data['email']).exists())
        response = self.client.post(self.url, data=self.registration_data)

        self.assertTrue(User.objects.filter(
            username=self.registration_data['username']).exists())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.get(
            username=self.registration_data['username']).is_active)

        response2 = self.client.post(self.url, data=self.registration_data)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data, {
                         'detail': 'Follow the link in mail to accept your registartion'})
        self.assertEqual(mock_send.call_count, 2)


class LoginAPIViewTestCase(AuthSettingsTest):
    def setUp(self):
        self.data = {
            "username": self.user.username,
            "password": "test_pas1"
        }
        self.url = reverse('login')

    def test_login_ok(self):
        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cookies.get('refresh'))
        self.assertTrue(response.cookies.get('access'))
        self.assertEqual(RefreshToken(response.cookies.get(
            'refresh').value).payload['username'], self.user.username)
        self.assertEqual(AccessToken(response.cookies.get(
            'access').value).payload['username'], self.user.username)

    def test_login_bad(self):
        data = self.data
        data.update({'username': 'beee'})

        response = self.client.post(self.url, data=data)

        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(response.cookies.get('refresh'))
        self.assertFalse(response.cookies.get('access'))
        self.assertEqual(
            response.data, {'error': 'User does not exist or given incorrect data'})


class LogoutAPIViewTestCase(AuthSettingsTest):
    def setUp(self):
        self.data = {
            "username": self.user.username,
            "password": "test_pas1"
        }
        self.url = reverse('logout')

    def test_logout_ok(self):
        response_login = self.client.post(reverse('login'), data=self.data)

        self.assertTrue(response_login.cookies.keys())

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.cookies.get('refresh').value)
        self.assertFalse(response.cookies.get('access').value)


class GetAccessTestCase(AuthSettingsTest):
    def setUp(self):
        self.data = {
            "username": self.user.username,
            "password": "test_pas1"
        }
        self.url = reverse('refresh')

    def test_get_new_tokens_ok(self):
        response_login = self.client.post(reverse('login'), data=self.data)
        refresh = response_login.cookies.get('refresh').value
        access = response_login.cookies.get('access').value
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(refresh, response.cookies.get('refresh').value)
        self.assertNotEqual(access, response.cookies.get('access').value)

    def test_get_new_tokens_bad(self):
        response_login = self.client.post(reverse('login'), data=self.data)

        with freeze_time(timezone.now() + timezone.timedelta(days=91)):
            response = self.client.get(self.url)

            self.assertNotEqual(response.status_code, 200)


class PasswordRecoveryAPIViewTestCase(AuthSettingsTest):
    @patch('api.tasks.send_celery_mail.delay')
    def test_send_mail(self, mock_send_mail):
        response = self.client.post(
            reverse('password-recovery'), data={'email': self.user.email})
        mock_send_mail.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, {'detail': 'We sent mail on your email to recovery password'})

    @patch('api.tasks.send_celery_mail.delay')
    def test_send_mail_user_disactive(self, mock_send_mail):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            reverse('password-recovery'), data={'email': self.user.email})
        mock_send_mail.assert_not_called()
        self.assertEqual(response.status_code, 406)
        self.assertEqual(
            response.data, {'error': 'User with this email is not active'})


class PasswordRecoveryConfirmAPIViewTestCase(AuthSettingsTest):
    def setUp(self):
        token_serializer = URLSafeTimedSerializer(
            secret_key=settings.SECRET_KEY)
        self.token = token_serializer.dumps(
            {'username': self.user.username}, salt=settings.PASSWORD_RECOVERY_SALT)
        self.url = reverse('confirm-password-recovery',
                           kwargs={'token': self.token})
        self.new_passws = {'new_password': 'new_pas1',
                           'new_password2': 'new_pas1'}

    def test_chpas_confirm(self):
        self.assertTrue(self.user.check_password('test_pas1'))

        response = self.client.post(self.url, data=self.new_passws)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user.check_password('test_pas1'))
        self.assertTrue(self.user.check_password(
            self.new_passws['new_password']))

    def test_chpas_confirm_bad_token(self):
        url = self.url[:-1]
        response = self.client.post(url, data=self.new_passws)
        self.assertEqual(response.status_code, 400)

    def test_chpas_confirm_token_expired(self):
        with freeze_time(timezone.now() + timezone.timedelta(seconds=60*60*4)):
            response = self.client.post(self.url, self.new_passws)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data, [ErrorDetail(
                string='Signature age 14400 > 10800 seconds', code='invalid')])

    def test_wrong_data(self):
        data = self.new_passws
        data.update({'new_password': 'asasf'})
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)


class RegistrationConfirmAPIViewTestCase(AuthSettingsTest):
    def setUp(self):
        token_serializer = URLSafeTimedSerializer(
            secret_key=settings.SECRET_KEY)
        self.token = token_serializer.dumps(
            {'username': self.user.username}, salt=settings.REGISTRATION_CONFIRM_SALT)
        self.url = reverse('confirm-registration',
                           kwargs={'token': self.token})
        self.user.is_active = False
        self.user.save()

    def test_confirm_reg_ok(self):
        self.assertFalse(self.user.is_active)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, {'detail': 'Registration successfully!'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_confirm_reg_bad_token(self):
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        response = self.client.get(self.url[:-3])
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.user.is_active)

    def test_confirm_reg_token_expired(self):
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        with freeze_time(timezone.now() + timezone.timedelta(seconds=60*60*4)):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.data, [ErrorDetail(string='Signature age 14400 > 10800 seconds', code='invalid')])
            self.assertFalse(self.user.is_active)
