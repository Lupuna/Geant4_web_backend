from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user, payload):
    refresh = RefreshToken.for_user(user)
    refresh.payload.update(payload)

    return str(refresh), str(refresh.access_token)
