from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

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

    def test_registration_ok(self):
        response = self.client.post(self.url, data=self.registration_data)

        self.assertTrue(User.objects.filter(
            username=self.registration_data['username']).exists())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(['refresh', 'access'], list(response.cookies.keys()))
        self.assertEqual(User.objects.filter(username=self.registration_data['username'])[0], User.objects.get(id=RefreshToken(
            response.cookies['refresh'].value).payload['user_id']))

    def test_registration_bad(self):
        data = self.registration_data
        data.update({'username': ''})

        response = self.client.post(self.url, data)

        self.assertNotEqual(response.status_code, 201)
        self.assertFalse(User.objects.filter(email=data['email']))
        self.assertFalse(response.cookies.keys())

    def test_registration_already_exists(self):
        data = self.registration_data
        data.update({'username': self.user.username})

        response = self.client.post(self.url, data=data)

        self.assertNotEqual(response.status_code, 200)


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

    def test_logout_not_logged_in(self):
        response = self.client.get(self.url)

        self.assertEqual(response.data, {'error': 'Refresh token require'})


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
    @patch('api.v1.tasks.send_celery_mail.delay')
    def test_send_mail(self, mock_send_mail):
        response = self.client.post(
            reverse('password-recovery'), data={'email': self.user.email})
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.data, {'error': 'This email was not verify'})

        self.user.is_email_verified = True
        self.user.save()
        response = self.client.post(
            reverse('password-recovery'), data={'email': self.user.email})
        mock_send_mail.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, {'detail': 'We sent mail on your email to password recovery'})


class PasswordRecoveryConfirmAPIViewTestCase(AuthSettingsTest):
    def setUp(self):
        token_serializer = URLSafeTimedSerializer(
            secret_key=settings.SECRET_KEY)
        self.token = token_serializer.dumps(
            {'email': self.user.email}, salt='password-recovery')
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
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.data, {'error': 'Invalid token'})

    def test_chpas_confirm_token_expired(self):
        with freeze_time(timezone.now() + timezone.timedelta(seconds=405)):
            response = self.client.post(self.url, self.new_passws)
            self.assertEqual(response.status_code, 406)
            self.assertEqual(response.data, {'error': 'Token expired'})

    def test_wrong_data(self):
        data = self.new_passws
        data.update({'new_password': 'asasf'})
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 400)


class EmailVerifyConfirmAPIViewTestCase(AuthSettingsTest):
    def setUp(self):
        token_serializer = URLSafeTimedSerializer(
            secret_key=settings.SECRET_KEY)
        self.token = token_serializer.dumps(
            {'email': self.user.email}, salt='email-verify')

    def test_email_verified_ok(self):
        self.assertFalse(self.user.is_email_verified)
        url = reverse('confirm-email-verify', kwargs={'token': self.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, {'detail': 'Email verified successfully'})
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_email_verify_bad_token(self):
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)
        url = reverse('confirm-email-verify',
                      kwargs={'token': self.token[:-1]})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 406)
        self.assertEqual(
            response.data, {'error': 'Invalid token'})
        self.assertFalse(self.user.is_email_verified)

    def test_email_verify_token_expired(self):
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)
        with freeze_time(timezone.now() + timezone.timedelta(seconds=305)):
            url = reverse('confirm-email-verify', kwargs={'token': self.token})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 406)
            self.assertEqual(
                response.data, {'error': 'Token expired'})
            self.assertFalse(self.user.is_email_verified)
