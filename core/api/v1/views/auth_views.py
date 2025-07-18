import datetime

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from api.tasks import send_celery_mail, send_celery_mail_advanced
from api.v1.serializers.auth_serializers import RegistrationSerializer, LoginSerializer
from api.v1.serializers.users_serializers import UserEmailSerializer, PasswordUpdateSerializer
from api.v1.serializers.utils import get_existing_conflicts
from users.auth.utils import get_tokens_for_user, put_token_on_blacklist, response_cookies, \
    get_token_info_or_return_failure, make_disposable_url
from users.models import User
from .mixins import CookiesMixin


@extend_schema(
    tags=['Auth endpoint']
)
class RegistrationAPIView(APIView):
    def get_user(self, serializer: RegistrationSerializer) -> User:
        serializer.is_valid(raise_exception=True)

        conflicts = get_existing_conflicts(serializer.validated_data)
        if conflicts:
            raise ValidationError({
                field: ["This value is already taken."] for field in conflicts
            })

        return serializer.save()

    @extend_schema(request=RegistrationSerializer)
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        user = self.get_user(serializer)
        disposable_url = make_disposable_url(settings.FRONTEND_URL + '/auth/registration/confirm/',
                                             settings.REGISTRATION_CONFIRM_SALT, {'username': user.username})
        message = f'Для завршения регистрации перейдите по ссылке\n{disposable_url}'
        send_celery_mail_advanced.delay(
            subject='Регистрация на сайте Geant4ru',
            message=message,
            recipients=[user.email],
            html_template='emails/verify_email.html',
            context={
                'result_link': disposable_url
            }
        )
        response = response_cookies(
            {'detail': 'Follow the link in mail to accept your registartion'},
            status.HTTP_200_OK
        )
        return response


@extend_schema(
    tags=['Auth endpoint']
)
class RegistrationConfirmAPIView(APIView):
    def get(self, request, token, *args, **kwargs):
        token_info = get_token_info_or_return_failure(
            token, 60 * 60 * 3, settings.REGISTRATION_CONFIRM_SALT)
        username = token_info.get('username')
        user = User.objects.get(username=username)
        user.is_active = True
        user.save()
        response = response_cookies(
            {'detail': 'Registration successfully!'}, status=status.HTTP_200_OK)
        return response


@extend_schema(
    tags=['Auth endpoint']
)
class LoginAPIView(APIView, CookiesMixin):
    authentication_classes = []

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        remember_user = request.data.get('remember_me', False)
        user = authenticate(request)
        check_request_cookies = self.check_request_cookies()

        if user is None or not user.is_active:
            response = response_cookies(
                {'error': 'User does not exist or given incorrect data'}, status.HTTP_400_BAD_REQUEST)
            if check_request_cookies:
                response = self.get_response_del_cookies(
                    response.data, response.status_code)
            return response

        tokens_data = [user]
        if not remember_user:
            tokens_data.append(
                {
                    'exp': int(
                        datetime.datetime.timestamp(timezone.now() + datetime.timedelta(seconds=3600))
                    )
                }
            )
        tokens = get_tokens_for_user(*tokens_data)
        self.response_cookies.update(tokens)
        response = self.get_response_set_cookies(
            {'detail': 'Logged in successfully'}, status.HTTP_200_OK)
        return response


@extend_schema(
    tags=['Auth endpoint']
)
class LogoutAPIView(APIView, CookiesMixin):
    def get_logout_response(self):
        try:
            put_token_on_blacklist(self.request_cookies.get('refresh'))
            response = self.get_response_del_cookies(
                {'detail': 'Logged out'}, status.HTTP_200_OK)
        except ValidationError:
            response = self.get_response_del_cookies(
                {'error': 'Invalid refresh token'}, status.HTTP_400_BAD_REQUEST)
        return response

    def get(self, request):
        self.check_request_cookies()
        response = self.get_logout_response()
        return response


@extend_schema(
    tags=['Auth endpoint']
)
class GetAccessTokenView(APIView, CookiesMixin):
    authentication_classes = []
    permission_classes = []

    def get(self, request, **kwargs):
        self.check_request_cookies('refresh', 'access')
        serializer = TokenRefreshSerializer(data=self.request_cookies)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            response = self.get_response_del_cookies(
                {'detail': 'Refresh token expired'}, status=status.HTTP_401_UNAUTHORIZED
            )
            return response
        tokens = {
            'refresh': serializer.validated_data['refresh'], 'access': serializer.validated_data['access']
        }
        self.response_cookies = tokens
        response = self.get_response_set_cookies(
            {'detail': 'Given new tokens'}, status=status.HTTP_200_OK)
        return response


@extend_schema(
    tags=['Auth endpoint']
)
class PasswordRecoveryAPIView(APIView):
    @extend_schema(request=UserEmailSerializer)
    def post(self, request, *args, **kwargs):
        serializer = UserEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_email = serializer.validated_data['email']
        user = User.objects.get(email=user_email)
        response = response_cookies(
            {'error': 'User with this email is not active'},
            status=status.HTTP_406_NOT_ACCEPTABLE
        )

        if user.is_active:
            dicposable_url = make_disposable_url(
                settings.FRONTEND_URL + '/auth/password_recovery/confirm/', settings.PASSWORD_RECOVERY_SALT,
                {'username': user.username})
            message = f'Для восстановления пароля перейдите по этой ссылке \n{dicposable_url}'
            send_celery_mail_advanced.delay(
                subject='Восстановление пароля для портала Gtant4ru',
                message=message,
                recipients=[user_email],
                html_template='emails/passsword_recovery.html',
                context={
                    'result_link': dicposable_url
                }
            )
            response = response_cookies(
                {'detail': 'We sent mail on your email to recovery password'},
                status=status.HTTP_200_OK
            )
        return response


@extend_schema(
    tags=['Auth endpoint']
)
class PasswordRecoveryConfirmAPIView(APIView):
    @extend_schema(request=PasswordUpdateSerializer)
    def post(self, request, token, *args, **kwargs):
        token_info = get_token_info_or_return_failure(
            token, 60 * 60 * 3, settings.PASSWORD_RECOVERY_SALT)
        username = token_info.get('username')
        user = User.objects.get(username=username)
        serializer = PasswordUpdateSerializer(
            instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = response_cookies(
            {'detail': 'Password recovered successfully'}, status=status.HTTP_200_OK)
        return response


@extend_schema(
    tags=['Auth endpoint']
)
class GetAuthInfoAPIView(APIView, CookiesMixin):
    def get(self, request, *args, **kwargs):
        response = Response(
            {'detail': bool(request.user and request.user.is_authenticated)})
        return response
