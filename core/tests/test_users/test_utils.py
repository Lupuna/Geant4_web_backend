from django.test import TestCase

from unittest.mock import MagicMock, patch

from users.auth import utils
from users.models import User

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


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
        self.assertEqual(
            str(refresh), BlacklistedToken.objects.get(id=1).token.token)
