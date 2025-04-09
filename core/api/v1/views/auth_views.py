import datetime

from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.exceptions import ValidationError

from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import timezone

from users.models import User

from api.v1.serializers.auth_serializers import RegistrationSerializer, LoginSerializer
from api.v1.serializers.users_serializers import UserEmailSerializer, PasswordUpdateSerializer

from users.auth.utils import get_tokens_for_user, put_token_on_blacklist, response_cookies, get_token_info_or_return_failure, make_disposable_url, send_disposable_mail

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
            response = response_cookies(
                {'detail': 'User created'}, status.HTTP_201_CREATED)

            return response

        return response_cookies(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Auth endpoint']
)
class LoginAPIView(APIView):
    authentication_classes = []

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        remember_user = request.data.get('remember_me', False)
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

        tokens_data = [user]

        if not remember_user:
            tokens_data.append({'exp': int(datetime.datetime.timestamp(
                timezone.now() + datetime.timedelta(seconds=3600)))})

        tokens = get_tokens_for_user(*tokens_data)
        response = response_cookies(
            {'detail': 'Logged in successfully'}, status.HTTP_200_OK, cookies_data=tokens)

        return response


@extend_schema(
    tags=['Auth endpoint']
)
class LogoutAPIView(APIView):
    def get(self, request):
        raw_refresh = request.COOKIES.get('refresh', None)
        cookie_to_remove = ['refresh', 'access']

        if not raw_refresh:
            return response_cookies({'error': 'Refresh token require'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            put_token_on_blacklist(refresh_token=raw_refresh)
        except ValidationError:
            return response_cookies({'error': 'Invalid refresh token'}, status.HTTP_400_BAD_REQUEST, cookies_data=cookie_to_remove, delete=True)

        return response_cookies({'detail': 'Logged out'}, status.HTTP_200_OK, cookies_data=cookie_to_remove, delete=True)


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


@extend_schema(
    tags=['Auth endpoint']
)
class PasswordRecoveryAPIView(APIView):
    @extend_schema(request=UserEmailSerializer)
    def post(self, request, *args, **kwargs):
        serializer = UserEmailSerializer(data=request.data)

        if serializer.is_valid():
            user_email = serializer.validated_data['email']
            user = User.objects.get(email=user_email)

            if user.is_email_verified:
                dicposable_url = make_disposable_url(
                    settings.FRONTEND_URL + '/auth/password_recovery/', 'password-recovery', {'email': user_email})
                message = f'For password recovery follow link\n{dicposable_url}'
                response = send_disposable_mail(
                    'Password recovery', message, [user_email])

                return response

            return response_cookies({'error': 'This email was not verify'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        return response_cookies({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Auth endpoint']
)
class PasswordRecoveryConfirmAPIView(APIView):
    @extend_schema(request=PasswordUpdateSerializer)
    def post(self, request, token, *args, **kwargs):
        token_info = get_token_info_or_return_failure(
            token, 300, request.resolver_match.view_name.split('-', 1)[1])

        if isinstance(token_info, dict):
            user_email = token_info.get('email')
            user = User.objects.get(email=user_email)
            serializer = PasswordUpdateSerializer(
                instance=user, data=request.data)

            if serializer.is_valid():
                serializer.save()

                return response_cookies({'detail': 'Password recovered successfully'}, status=status.HTTP_200_OK, cookies_data=['access', 'refresh'], delete=True)

            return response_cookies({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return token_info


@extend_schema(
    tags=['Auth endpoint']
)
class EmailVerifyConfirmAPIView(APIView):
    def get(self, request, token, *args, **kwargs):
        token_info = get_token_info_or_return_failure(
            token, 300, request.resolver_match.view_name.split('-', 1)[1])

        if isinstance(token_info, dict):
            user_email = token_info.get('email')
            user = User.objects.get(email=user_email)
            user.is_email_verified = True
            user.save()

            return response_cookies({'detail': 'Email verified successfully'}, status=status.HTTP_200_OK)

        return token_info


@extend_schema(
    tags=['Auth endpoint']
)
class GetAuthInfoAPIView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        refresh = request.COOKIES.get('refresh', None)
        access = request.COOKIES.get('access', None)

        if refresh and access:
            return response_cookies({'detail': True}, status=status.HTTP_200_OK)

        return response_cookies({'detail': False}, status=status.HTTP_401_UNAUTHORIZED)
