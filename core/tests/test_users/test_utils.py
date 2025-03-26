from django.test import TestCase
from django.conf import settings
from django.utils import timezone

from unittest.mock import MagicMock, patch

from users.auth import utils
from users.models import User

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework.response import Response

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from freezegun import freeze_time


class TokenUtilsTestCase(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'test_username',
            'email': 'test_email@gmail.com',
            'first_name': 'test_first_name',
            'last_name': 'test_last_name',
            'password': 'test_password'
        }
        self.user = User.objects.create(**self.user_data)

    def test_get_tokens(self):
        tokens = utils.get_tokens_for_user(self.user)
        self.assertEqual(RefreshToken(tokens['refresh']).payload.get(
            'user_id'), RefreshToken.for_user(self.user).payload.get('user_id'))

    def test_put_token_on_blacklist(self):
        refresh = RefreshToken.for_user(self.user)
        utils.put_token_on_blacklist(str(refresh))

        self.assertTrue(OutstandingToken.objects.filter(
            token=str(refresh)).exists())


class TokenInfoTestCase(TestCase):
    def test_get_token_info_or_return_failure(self):
        token_ser = URLSafeTimedSerializer(secret_key=settings.SECRET_KEY)
        token = token_ser.dumps(
            {'email': 'test_email@gmail.com'}, salt='test-salt')

        token_info_ok = utils.get_token_info_or_return_failure(
            token, 300, salt='test-salt')
        self.assertIsInstance(token_info_ok, dict)

        with freeze_time(timezone.now() + timezone.timedelta(seconds=400)):
            token_expired_info = utils.get_token_info_or_return_failure(
                token, 300, salt='test-salt')
            self.assertIsInstance(token_expired_info, Response)
            self.assertEqual(token_expired_info.data, {
                             'error': 'Token expired'})

        token_bad_sign_info = utils.get_token_info_or_return_failure(
            token, 200, 'bad-salt')
        self.assertIsInstance(token_bad_sign_info, Response)
        self.assertEqual(token_bad_sign_info.data, {'error': 'Invalid token'})


class MailSenderTestCase(TestCase):
    def test_send_disposable_mail(self):
        pass
