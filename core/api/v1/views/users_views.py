import os

import loguru
from django.http import FileResponse
from rest_framework.parsers import MultiPartParser
from rest_framework.viewsets import GenericViewSet, ViewSet
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from api.v1.serializers.users_serializers import (
    UserProfileSerializer,
    LoginUpdateSerializer,
    UserProfileCommonUpdateSerializer, UserProfileImageSerializer,
)
from api.v1.serializers.examples_serializers import ExampleForUserSerializer
from file_client.exceptions import FileClientException
from file_client.profile_image_client import ProfileImageRendererClient
from file_client.schema import image_schema
from file_client.tasks import render_and_upload_task, render_and_update_task
from file_client.utils import handle_file_upload

from users.models import User
from users.auth.utils import response_cookies, get_tokens_for_user, put_token_on_blacklist, send_disposable_mail, \
    make_disposable_url

from geant_examples.models import UserExampleCommand

from drf_spectacular.utils import extend_schema

from django.conf import settings


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
        serializer = UserProfileImageSerializer(data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            old_path = handle_file_upload(serializer.validated_data.get('image'))
            render_and_upload_task.delay(old_path, str(user.uuid))

            return Response({"detail": "Image processing started"}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        request=image_schema
    )
    def update(self, request):
        user = self.get_user()
        serializer = UserProfileImageSerializer(data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            old_path = handle_file_upload(serializer.validated_data.get('image'))
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
            response = FileResponse(client.download(), as_attachment=True, filename=str(user.uuid)+f'.{client.format}')
        except FileClientException as e:
            return Response(e.error, status=status.HTTP_404_NOT_FOUND)
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

    @action(methods=['get', ], detail=False, url_path='email_verify', url_name='email-verify')
    def email_verify(self, request, *args, **kwargs):
        user = request.user

        if not user.is_email_verified:
            dicposable_url = make_disposable_url(
                settings.FRONTEND_URL + '/auth/email_verify/', 'email-verify', {'email': user.email})
            message = f'For email verify follow link\n{dicposable_url}'
            response = send_disposable_mail(
                'Email verify', message, [user.email])

            return response

        return response_cookies({'error': 'Your email already verified'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['UserProfile']
)
class UserExampleView(GenericAPIView):
    queryset = UserExampleCommand.objects.prefetch_related(
        'example_command__example')
    serializer_class = ExampleForUserSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        user_ex_commands = self.queryset.filter(user=user)
        serializer = self.serializer_class(
            instance=user_ex_commands, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
