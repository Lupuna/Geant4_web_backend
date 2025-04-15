from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from rest_framework.response import Response

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from loguru import logger

from django.contrib.auth import get_user_model
from django.conf import settings


User = get_user_model()


def get_tokens_for_user(user, payload=None):
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    username_field = User.USERNAME_FIELD
    refresh.payload.update({username_field: getattr(user, username_field)})
    access.payload.update({username_field: getattr(user, username_field)})

    if payload:
        refresh.payload.update(payload)
        access.payload.update(payload)

    return {'refresh': str(refresh), 'access': str(access)}


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
                    key=key, value=cookies_data[key], httponly=True, secure=True, samesite='None')
        else:
            for key in cookies_data:
                response.delete_cookie(key=key)

    return response


def get_token_info_or_return_failure(raw_token, token_expire_time: int, salt) -> (dict | Response):
    try:
        decoded_token_serializer = URLSafeTimedSerializer(
            secret_key=settings.SECRET_KEY)
        decoded_token = decoded_token_serializer.loads(
            raw_token, salt=salt, max_age=token_expire_time)
    except SignatureExpired:
        return response_cookies({'error': 'Token expired'}, status=status.HTTP_406_NOT_ACCEPTABLE)
    except BadSignature:
        return response_cookies({'error': 'Invalid token'}, status=status.HTTP_406_NOT_ACCEPTABLE)

    return decoded_token


def make_disposable_url(base_path: str, token_salt: str, payload: dict):
    token_serializer = URLSafeTimedSerializer(
        secret_key=settings.SECRET_KEY)
    token = token_serializer.dumps(
        payload, salt=token_salt)
    disposable_url = base_path + token

    return disposable_url
