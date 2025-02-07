from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError

from loguru import logger


def get_tokens_for_user(user, payload=None):
    refresh = RefreshToken.for_user(user)
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
