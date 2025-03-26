from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import status

from api.v1.serializers.users_serializers import (
    UserProfileSerializer,
    LoginUpdateSerializer,
    UserProfileCommonUpdateSerializer,
)
from api.v1.serializers.examples_serializers import ExampleForUserSerializer

from users.models import User
from users.auth.utils import response_cookies, get_tokens_for_user, put_token_on_blacklist, send_disposable_mail

from geant_examples.models import Example, Tag, UserExample

from drf_spectacular.utils import extend_schema

from django.db.models import Prefetch


@extend_schema(
    tags=['UserProfile']
)
class UserProfileViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated, )
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
            {'detail': 'Profile was deleted successfully'}, status.HTTP_200_OK, cookies_data=cookies_to_delete, delete=True)

        return response


@extend_schema(
    tags=['UserProfile']
)
class UserProfileUpdateImportantInfoViewSet(GenericViewSet):
    permission_classes = (IsAuthenticated, )

    @extend_schema(responses=ExampleForUserSerializer)
    @action(methods=['get', ], detail=False, url_path='my_examples', url_name='user-examples')
    def get_user_examples(self, request, **kwargs):
        user = request.user

        examples = Example.objects.filter(users__id=user.id).only('title').prefetch_related(
            Prefetch(
                'example_users',
                queryset=UserExample.objects.filter(
                    user=user.id).only('example', 'status'),
                to_attr='example_user'
            ),
            'tags'
        ).distinct()
        serializer = ExampleForUserSerializer(instance=examples, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

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
            response = send_disposable_mail(
                user.email, 'email verify', 'api.v1.tasks.send_celery_mail')

            return response

        return response_cookies({'error': 'Your email already verified'}, status=status.HTTP_400_BAD_REQUEST)
