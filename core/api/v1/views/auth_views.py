from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenRefreshView

from django.contrib.auth import authenticate

from users.models import User

from api.v1.serializers.auth_serializers import RegistrationSerializer, LoginSerializer
from users.auth.utils import get_tokens_for_user

from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=['Auth endpoint']
)
class RegistrationAPIView(APIView):
    @extend_schema(request=RegistrationSerializer)
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh, access = get_tokens_for_user(
                user, {'username': user.username})

            return Response({'refresh': str(refresh), 'access': str(access)}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Auth endpoint']
)
class LoginAPIView(APIView):
    authentication_classes = []

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        user = authenticate(request)
        if user is None:
            return Response({'error': 'User does not exist or given incorrect data'}, status=status.HTTP_400_BAD_REQUEST)

        refresh, access = get_tokens_for_user(
            user, payload={'username': user.username})

        response = Response(
            {'detail': 'Logged in successfully'}, status=status.HTTP_200_OK)
        # не забыть поставить secure=True когда будет https
        response.set_cookie(key='access_token', value=access,
                            httponly=True, secure=False, samesite='Lax')
        response.set_cookie(key='refresh_token', value=refresh,
                            httponly=True, secure=False, samesite='Lax')

        return response


class LogoutAPIView(APIView):
    pass


@extend_schema(
    tags=['Auth endpoint']
)
class GetAccessByRefreshView(TokenRefreshView):
    pass
