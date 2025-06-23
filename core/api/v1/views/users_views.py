from django.conf import settings
from django.db.utils import IntegrityError
from django.http import FileResponse

from drf_spectacular.utils import extend_schema

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ViewSet

from api.v1.serializers.examples_serializers import ExampleForUserSerializer
from api.v1.serializers.users_serializers import (
    UserProfileSerializer,
    LoginUpdateSerializer,
    UserProfileCommonUpdateSerializer,
    UserProfileImageSerializer,
    PasswordProfileUpdateSerializer
)
from file_client.exceptions import FileClientException
from file_client.files_clients import ProfileImageRendererClient
from file_client.schema import image_schema
from file_client.tasks import render_and_upload_profile_image_task, render_and_update_profile_image_task
from file_client.utils import handle_file_upload

from geant_examples.documents import ExampleDocument
from geant_examples.models import UserExampleCommand

from users.auth.utils import (
    response_cookies,
    get_tokens_for_user,
    put_token_on_blacklist,
    get_token_info_or_return_failure
)
from users.models import User

from .mixins import ElasticMixin, QueryParamsMixin, CookiesMixin


@extend_schema(
    tags=['UserProfile']
)
class UserProfileViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet, CookiesMixin):
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
        self.check_request_cookies()
        response = self.get_response_del_cookies(
            {'detail': 'Profile was deleted successfully'}, status.HTTP_200_OK)
        return response


@extend_schema(
    tags=['UserProfile']
)
class ConfirmEmailUpdateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def try_update_email(self, user, new_email):
        try:
            user.email = new_email
            user.save()
        except IntegrityError:
            raise ValidationError('This email already in use')

    def get(self, request, token, *args, **kwargs):
        token_info = get_token_info_or_return_failure(
            token, 60 * 60 * 3, settings.EMAIL_UPDATE_SALT)
        new_email = token_info.get('new_email')
        user = request.user
        response = response_cookies(
            {'detail': 'Email updated successfully'}, status=status.HTTP_200_OK)
        self.try_update_email(user, new_email)
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
            'get': 'retrieve',
            'delete': 'destroy'
        }

    @extend_schema(
        request=image_schema
    )
    def create(self, request):
        user = self.get_user()
        serializer = UserProfileImageSerializer(
            data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_path = handle_file_upload(
            serializer.validated_data.get('image'))
        render_and_upload_profile_image_task.delay(old_path, str(user.uuid))
        return Response({"detail": "Image processing started"}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        request=image_schema
    )
    def update(self, request):
        user = self.get_user()
        serializer = UserProfileImageSerializer(
            data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_path = handle_file_upload(
            serializer.validated_data.get('image'))
        render_and_update_profile_image_task.delay(old_path, str(user.uuid))
        return Response({"detail": "Image processing started"}, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request):
        user = self.get_user()
        ProfileImageRendererClient(name=str(user.uuid)).delete()
        return Response({"detail": "Image deleted"}, status=status.HTTP_200_OK)

    def retrieve(self, request):
        user = self.get_user()
        client = ProfileImageRendererClient(name=str(user.uuid))
        try:
            response = FileResponse(client.download(), as_attachment=True, filename=str(
                user.uuid) + f'.{client.format}')
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
        serializer.is_valid(raise_exception=True)
        user_new_username = serializer.save()
        tokens = get_tokens_for_user(user_new_username)
        response = response_cookies(
            {'detail': 'Username updated successfully'}, status.HTTP_200_OK, tokens)
        return response

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
class UserExampleView(GenericAPIView, ElasticMixin, QueryParamsMixin):
    queryset = UserExampleCommand.objects.prefetch_related(
        'example_command__example')
    serializer_class = ExampleForUserSerializer
    elastic_document = ExampleDocument
    order_by = 'creation_date'

    def get_queryset(self):
        document_class = self.get_elastic_document_class()
        search = document_class.search()
        self.setup_elastic_document_conf()
        after_search = self.elastic_search(self.request, search)
        after_filter = self.elastic_filter(self.request, after_search)
        ex_queryset = after_filter.to_queryset()
        user_ex_commands = super().get_queryset().filter(
            user=self.request.user, example_command__example__in=ex_queryset)
        user_ex_commands = self.sort_by_ord(user_ex_commands)
        return user_ex_commands

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=self.get_queryset(), many=True
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['User check is_staff']
)
class UserStaff(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response({'is_staff': request.user.is_staff})
