from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class JWTAuthenticationByCookies(JWTAuthentication):
    def authenticate(self, request):
        if not request.COOKIES:
            return None

        refresh = request.COOKIES.get('refresh')
        access = request.COOKIES.get('access')

        if not (refresh and access):
            return None

        validated_token = self.get_validated_token(access)
        user = self.get_user(validated_token)

        return user, validated_token
