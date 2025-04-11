from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import BaseAuthentication


class JWTAuthenticationByCookie(BaseAuthentication):
    jwt_auth_obj = JWTAuthentication()

    def authenticate(self, request):
        access = request.COOKIES.get('access', None)

        if not access:
            return None

        validated_token = self.jwt_auth_obj.get_validated_token(access)
        user = self.jwt_auth_obj.get_user(validated_token)

        return user, validated_token
