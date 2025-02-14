from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from api.v1.serializers.examples_serializers import ExampleSerializer, TagSerializer

from users.models import User

from geant_examples.models import Example, Tag, UserExample

from drf_spectacular.utils import extend_schema

from rest_framework.permissions import IsAuthenticated


@extend_schema(
    tags=['Example ViewSet']
)
class ExampleViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, )
    serializer_class = ExampleSerializer
    queryset = Example.objects.all()
