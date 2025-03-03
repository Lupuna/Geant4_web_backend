from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import status
from rest_framework.generics import get_object_or_404


from api.v1.serializers.users_serializers import UserProfileSerializer, LoginUpdateSerializer, PasswordUpdateSerializer, UserProfileCommonUpdateSerializer
from api.v1.serializers.examples_serializers import ExampleForUserSerializer

from users.models import User
from users.auth.utils import response_cookies, get_tokens_for_user, put_token_on_blacklist

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
        raw_access = self.request.COOKIES.get('access')
        access = AccessToken(raw_access)
        username = access.payload.get(User.USERNAME_FIELD)
        obj = get_object_or_404(User, username=username)

        return obj

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

    @action(methods=['get', ], detail=False, url_path='my_examples', url_name='user-examples')
    def get_user_examples(self, request, **kwargs):
        raw_token = request.COOKIES.get('access')
        access_token = AccessToken(raw_token)
        user_id = access_token.get('user_id')

        examples = Example.objects.filter(users__id=user_id).only('title').prefetch_related(
            Prefetch(
                'example_users',
                queryset=UserExample.objects.filter(
                    user=user_id).only('example', 'status'),
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

    @extend_schema(request=PasswordUpdateSerializer)
    @action(methods=['post', ], detail=False, url_path='update_password', url_name='update-password')
    def update_password(self, request, *args, **kwargs):
        user = request.user
        serializer = PasswordUpdateSerializer(instance=user, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return response_cookies({'detail': 'Password updated successfully'}, status.HTTP_200_OK)

        return response_cookies(serializer.errors, status.HTTP_400_BAD_REQUEST)
