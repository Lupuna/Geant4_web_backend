from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from rest_framework.response import Response

from loguru import logger

from django.contrib.auth import get_user_model


User = get_user_model()


def get_tokens_for_user(user, payload=None):
    refresh = RefreshToken.for_user(user)
    username_field = User.USERNAME_FIELD
    refresh.payload.update({username_field: getattr(user, username_field)})

    if payload:
        refresh.payload.update(payload)

    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


def put_token_on_blacklist(refresh_token):
    try:
        old_token = RefreshToken(refresh_token)
        old_token.blacklist()
    except TokenError as e:
        logger.critical(
            f"TokenError: {e}. It might be a potential security threat.")
        raise ValidationError({'error': 'Invalid refresh token'})


def response_cookies(response_data, status, cookies_data=None, delete=False):
    response = Response(response_data, status)

    if cookies_data:

        if not delete:
            for key in cookies_data:
                response.set_cookie(
                    key=key, value=cookies_data[key], httponly=True, secure=True, samesite='Lax')
        else:
            for key in cookies_data:
                response.delete_cookie(key=key)

    return response
