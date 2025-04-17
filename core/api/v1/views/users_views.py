from django.http import FileResponse
from django.conf import settings
from django.db.utils import IntegrityError

from rest_framework.parsers import MultiPartParser
from rest_framework.viewsets import GenericViewSet, ViewSet
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .mixins import ElasticMixin

from api.v1.serializers.users_serializers import (
    UserProfileSerializer,
    LoginUpdateSerializer,
    UserProfileCommonUpdateSerializer,
    UserProfileImageSerializer,
    PasswordProfileUpdateSerializer
)
from api.v1.serializers.examples_serializers import ExampleForUserSerializer

from file_client.exceptions import FileClientException
from file_client.profile_image_client import ProfileImageRendererClient
from file_client.schema import image_schema
from file_client.tasks import render_and_upload_task, render_and_update_task
from file_client.utils import handle_file_upload

from users.models import User
from users.auth.utils import response_cookies, get_tokens_for_user, put_token_on_blacklist, get_token_info_or_return_failure

from geant_examples.models import UserExampleCommand
from geant_examples.documents import ExampleDocument

from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=['UserProfile']
)
class UserProfileViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()

    def get_serializer(self, *args, **kwargs):
        if self.request.method in ['GET', ]:
            return UserProfileSerializer(*args, **kwargs)
        elif self.request.method in ['PATCH', ]:
            return UserProfileCommonUpdateSerializer(*args, **kwargs)

    def get_object(self):
        return self.request.user

    @classmethod
    def get_actions(cls):
        return {
            'get': 'retrieve',
            'patch': 'update',
            'delete': 'destroy'
        }

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        cookies_to_delete = ('access', 'refresh')
        response = response_cookies(
            {'detail': 'Profile was deleted successfully'}, status.HTTP_200_OK, cookies_data=cookies_to_delete,
            delete=True)

        return response


@extend_schema(
    tags=['UserProfile']
)
class ConfirmEmailUpdateAPIView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, token, *args, **kwargs):
        token_info = get_token_info_or_return_failure(
            token, 60 * 60, settings.EMAIL_UPDATE_SALT)
        new_email = token_info.get('new_email')
        user = request.user
        user.email = new_email

        try:
            user.save()
        except IntegrityError:
            return response_cookies({'error': 'This email already in use'}, status=status.HTTP_400_BAD_REQUEST)

        return response_cookies({'detail': 'Email updated successfully'}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['UserProfile']
)
class UserProfileImageViewSet(ViewSet):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)

    def get_user(self):
        return self.request.user

    @classmethod
    def get_action_map(cls):
        return {
            'post': 'create',
            'patch': 'update',
            'get': 'download',
            'delete': 'destroy'
        }

    @extend_schema(
        request=image_schema
    )
    def create(self, request):
        user = self.get_user()
        serializer = UserProfileImageSerializer(
            data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            old_path = handle_file_upload(
                serializer.validated_data.get('image'))
            render_and_upload_task.delay(old_path, str(user.uuid))

            return Response({"detail": "Image processing started"}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        request=image_schema
    )
    def update(self, request):
        user = self.get_user()
        serializer = UserProfileImageSerializer(
            data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            old_path = handle_file_upload(
                serializer.validated_data.get('image'))
            render_and_update_task.delay(old_path, str(user.uuid))

            return Response({"detail": "Image processing started"}, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request):
        user = self.get_user()
        ProfileImageRendererClient(name=str(user.uuid)).delete()
        return Response({"detail": "Image deleted"}, status=status.HTTP_200_OK)

    def download(self, request):
        user = self.get_user()
        client = ProfileImageRendererClient(name=str(user.uuid))
        try:
            response = FileResponse(client.download(), as_attachment=True, filename=str(
                user.uuid)+f'.{client.format}')
        except FileClientException as e:
            return Response(e.error, status=status.HTTP_200_OK)
        return response


@extend_schema(
    tags=['UserProfile']
)
class UserProfileUpdateImportantInfoViewSet(GenericViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = None

    @extend_schema(request=LoginUpdateSerializer)
    @action(methods=['post', ], detail=False, url_path='update_username', url_name='update-username')
    def username_update(self, request, *args, **kwargs):
        put_token_on_blacklist(request.COOKIES.get('refresh'))
        user = request.user
        serializer = LoginUpdateSerializer(instance=user, data=request.data)

        if serializer.is_valid():
            user_new_username = serializer.save()
            tokens = get_tokens_for_user(user_new_username)
            response = response_cookies(
                {'detail': 'Username updated successfully'}, status.HTTP_200_OK, tokens)

            return response

        return response_cookies(serializer.errors, status.HTTP_400_BAD_REQUEST)

    @extend_schema(request=PasswordProfileUpdateSerializer)
    @action(methods=['post', ], detail=False, url_path='update_password', url_name='update-password')
    def update_password(self, request, *args, **kwargs):
        user = request.user
        serializer = PasswordProfileUpdateSerializer(
            instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return response_cookies({'detail': 'Password updated successfully'}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['UserProfile']
)
class UserExampleView(GenericAPIView, ElasticMixin):
    queryset = UserExampleCommand.objects.prefetch_related(
        'example_command__example')
    serializer_class = ExampleForUserSerializer
    elastic_document = ExampleDocument

    def get_queryset(self):
        search = self.elastic_document.search()
        after_search = self.elastic_search(self.request, search)
        after_filter = self.elastic_filter(self.request, after_search)
        ex_queryset = after_filter.to_queryset()
        ordering = self.request.query_params.get('ord', None)
        order_param = None

        if ordering == 'asc':
            order_param = 'creation_date'
        elif ordering == 'desc':
            order_param = '-creation_date'

        user_ex_commands = super().get_queryset().filter(
            user=self.request.user, example_command__example__in=ex_queryset)

        if order_param:
            return user_ex_commands.order_by(order_param)

        return user_ex_commands

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=self.get_queryset(), many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
