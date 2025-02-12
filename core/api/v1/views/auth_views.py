from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import authenticate

from users.models import User

from api.v1.serializers.auth_serializers import RegistrationSerializer, LoginSerializer

from users.auth.utils import get_tokens_for_user, put_token_on_blacklist, response_cookies

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
            tokens = get_tokens_for_user(user, {'username': user.username})
            response = response_cookies(
                {'detail': 'User created'}, status.HTTP_201_CREATED, cookies_data=tokens)

            return response

        return response_cookies(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Auth endpoint']
)
class LoginAPIView(APIView):
    authentication_classes = []

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        user = authenticate(request)

        if user is None:
            potential_refresh = request.COOKIES.get('refresh', None)
            potential_access = request.COOKIES.get('access', None)

            if (potential_access or potential_refresh):
                cookie_keys = ['refresh', 'access']
                response = response_cookies({'error': 'User does not exist or given incorrect data'},
                                            status.HTTP_400_BAD_REQUEST, cookies_data=cookie_keys, delete=True)

            response = response_cookies(
                {'error': 'User does not exist or given incorrect data'}, status.HTTP_400_BAD_REQUEST)

            return response

        tokens = get_tokens_for_user(user, payload={'username': user.username})
        response = response_cookies(
            {'detail': 'Logged in successfully'}, status.HTTP_200_OK, cookies_data=tokens)

        return response


@extend_schema(
    tags=['Auth endpoint']
)
class LogoutAPIView(APIView):
    def get(self, request):
        raw_refresh = request.COOKIES.get('refresh', None)
        if not raw_refresh:
            return response_cookies({'error': 'Refresh token require'}, status=status.HTTP_400_BAD_REQUEST)

        put_token_on_blacklist(refresh_token=raw_refresh)
        cookie_to_remove = ['refresh', 'access']
        response = response_cookies(
            {'detail': 'Logged out'}, status.HTTP_200_OK, cookies_data=cookie_to_remove, delete=True)

        return response


@extend_schema(
    tags=['Auth endpoint']
)
class GetAccessTokenView(APIView):
    def get(self, request, **kwargs):
        raw_refresh = request.COOKIES.get('refresh', None)
        serializer = TokenRefreshSerializer(data={'refresh': raw_refresh})
        if serializer.is_valid():
            tokens = {
                'refresh': serializer.validated_data['refresh'], 'access': serializer.validated_data['access']}
            response = response_cookies(
                {'detail': 'Given new tokens'}, status=status.HTTP_200_OK, cookies_data=tokens)

            return response

        return response_cookies({'error(token validating)': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
