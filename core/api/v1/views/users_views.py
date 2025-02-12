from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

from api.v1.serializers.users_serializers import UserProfileSerializer
from api.v1.serializers.examples_serializers import ExampleForUserSerializer

from users.models import User
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
