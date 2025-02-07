from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from itsdangerous import BadSignature, SignatureExpired

from freezegun import freeze_time

from unittest.mock import patch, MagicMock

from users.models import User


class RegistrationAPIViewTestCase(TestCase):
    def setUp(self):
        self.registration_data = {
            'username': 'test_username',
            'tag': 'test_tag_9',
            'email': 'test_email@gmail.com',
            'first_name': 'test_first_name',
            'last_name': 'test_last_name',
            'password': 'test_password',
            'password2': 'test_password'
        }
        self.client = APIClient()
        self.url = reverse('registration')

    def test_registration_ok(self):
        response = self.client.post(self.url, data=self.registration_data)
        self.assertEqual(response.status_code, 201)
        print(response.cookies)
