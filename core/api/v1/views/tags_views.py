from geant_examples.models import Tag

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from api.v1.serializers.examples_serializers import TagAPISerializer

from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=['Tags ViewSet']
)
class TagViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    queryset = Tag.objects.all()
    serializer_class = TagAPISerializer
