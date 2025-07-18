from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from api.v1.serializers.auth_serializers import LoginSerializer


User = get_user_model()


class LoginByUsernameBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        data = getattr(request, 'data', request.POST)
        serializer = LoginSerializer(data=data)

        if serializer.is_valid():
            user = self.get_user(serializer.validated_data['username'])

            if user and user.check_password(serializer.validated_data['password']):
                return user

            return None

        return None

    def get_user(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        return user
