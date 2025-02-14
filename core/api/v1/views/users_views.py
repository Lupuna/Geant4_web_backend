from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework import status

from api.v1.serializers.users_serializers import UserProfileSerializer, LoginUpdateSerializer, PasswordUpdateSerializer
from api.v1.serializers.examples_serializers import ExampleForUserSerializer

from users.models import User
from users.auth.utils import response_cookies, get_tokens_for_user, put_token_on_blacklist

from geant_examples.models import Example, Tag, UserExample

from drf_spectacular.utils import extend_schema

from django.forms.models import model_to_dict
from django.db.models import Prefetch


@extend_schema(
    tags=['UserProfile']
)
class UserProfileViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()

    @action(methods=['get', ], detail=False, url_path='user_examples', url_name='user-examples')
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
        serializer = ExampleForUserSerializer(
            instance=examples, many=True)

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
