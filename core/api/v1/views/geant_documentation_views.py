from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from api.v1.serializers.geant_documentation_serializers import ArticleListSerializer, ArticleSerializer
from api.v1.views.mixins import ElasticMixin
from core.permissions import IsStaffPermission
from geant_documentation.documents import ArticleDocument
from geant_documentation.models import Article


@extend_schema(
    tags=['Documentations endpoints']
)
class ArticleViewSet(ElasticMixin, ModelViewSet):
    elastic_document = ArticleDocument

    def get_queryset(self):
        if self.action == 'list':
            search = self.elastic_document.search()
            after_search = self.elastic_search(self.request, search)
            after_filter = self.elastic_filter(self.request, after_search)
            return after_filter.to_queryset()

        return Article.objects.prefetch_related('category', 'subscriptions', 'chapter').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer

        return ArticleSerializer

    # def get_permissions(self):
    #     if self.action in ['list', 'retrieve']:
    #         permission_classes = [AllowAny]
    #     else:
    #         permission_classes = [IsAuthenticated, IsStaffPermission]
    #     return [permission() for permission in permission_classes]

    # def perform_create(self, serializer):
    #     try:
    #         super().perform_create(serializer)
    #     except DjangoValidationError as e:
    #         raise DRFValidationError({'error': e.messages})
    #     except IntegrityError as e:
    #         raise DRFValidationError({'error': 'duplicate paragraph_order for this article'})