import importlib

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from rest_framework.response import Response

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from loguru import logger

from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch


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


def send_disposable_mail(recipient_email, reason, task_path) -> Response:
    base_path_name = reason.replace(' ', '-')
    disposable_link_view_path_name = 'confirm-' + base_path_name
    token_serializer = URLSafeTimedSerializer(
        secret_key=settings.SECRET_KEY)
    token = token_serializer.dumps(
        {'email': recipient_email}, salt=base_path_name)

    try:
        recovery_url = settings.WEB_BACKEND_URL + \
            reverse(disposable_link_view_path_name,
                    kwargs={'token': token})
    except NoReverseMatch:
        return response_cookies({'error': f'View or corresponding path for {reason} does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    decomposed_path_to_task = task_path.split('.')
    mail_task_name = decomposed_path_to_task[-1]
    module = '.'.join(decomposed_path_to_task[:-1])
    mail_task = getattr(importlib.import_module(module), mail_task_name)

    mail_task.delay(subject=reason.capitalize(), message=f'For {reason} follow this link\n{recovery_url}', from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[
                    recipient_email], auth_user=settings.EMAIL_HOST_USER, auth_password=settings.EMAIL_HOST_PASSWORD)

    return response_cookies({'detail': f'We sent mail on your email to {reason}'}, status=status.HTTP_200_OK)
