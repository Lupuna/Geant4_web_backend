from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, CreateModelMixin
from api.v1.serializers.uesrs_serialisers import UserProfileSerializer
from users.models import User
from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=['UserProfile']
)
class UserProfileViewSet(RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, CreateModelMixin, GenericViewSet):
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()
