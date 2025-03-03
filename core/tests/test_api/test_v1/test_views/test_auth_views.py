from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from itsdangerous import BadSignature, SignatureExpired

from freezegun import freeze_time

from unittest.mock import patch, MagicMock

from users.models import User

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
