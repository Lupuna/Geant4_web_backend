from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from api.v1.serializers.geant_documentation_serializers import (
    ArticleListSerializer,
    ArticleSerializer,
    SubscriptionSerializer,
    ElementSerializer,
    ChapterSerializer,
    CategorySerializer
)
from api.v1.views.mixins import ElasticMixin, ValidationHandlingMixin
from core.permissions import IsStaffPermission
from geant_documentation.documents import ArticleDocument
from geant_documentation.models import Article, Subscription, Chapter, Category, Element


@extend_schema(
    tags=['Documentation Chapters']
)
class ChapterViewSet(ModelViewSet):
    serializer_class = ChapterSerializer
    queryset = Chapter.objects.all()


@extend_schema(
    tags=['Documentation Categories']
)
class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


@extend_schema(
    tags=['Documentation Elements']
)
class ElementViewSet(ValidationHandlingMixin, ModelViewSet):
    serializer_class = ElementSerializer

    def get_queryset(self):
        return Element.objects.prefetch_related('files').filter(
            subscription=self.kwargs['subscription_pk']
        )

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsStaffPermission]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer, **kwargs):
        url_variables = {
            'subscription_id': self.kwargs['subscription_pk'],
        }
        super().perform_create(serializer, **url_variables)

    def perform_update(self, serializer, **kwargs):
        url_variables = {
            'subscription_id': self.kwargs['subscription_pk']
        }
        super().perform_update(serializer, **url_variables)


@extend_schema(
    tags=['Documentations Subscriptions']
)
class SubscriptionViewSet(ValidationHandlingMixin, ModelViewSet):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.prefetch_related('elements', 'elements__files').filter(
            article=self.kwargs['article_pk']
        )

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsStaffPermission]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer, **kwargs):
        url_variables = {
            'article_id': self.kwargs['article_pk']
        }
        super().perform_create(serializer, **url_variables)

    def perform_update(self, serializer, **kwargs):
        url_variables = {
            'article_id': self.kwargs['article_pk']
        }
        super().perform_update(serializer, **url_variables)


@extend_schema(
    tags=['Documentations Articles']
)
class ArticleViewSet(ElasticMixin, ValidationHandlingMixin, ModelViewSet):
    elastic_document = ArticleDocument

    def get_queryset(self):
        if self.action == 'list':
            search = self.elastic_document.search()
            after_search = self.elastic_search(self.request, search)
            after_filter = self.elastic_filter(self.request, after_search)
            return after_filter.to_queryset()

        return Article.objects.select_related('category', 'chapter').prefetch_related(
            'subscriptions',
            'subscriptions__elements',
            'subscriptions__elements__files'
        ).all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer

        return ArticleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsStaffPermission]
        return [permission() for permission in permission_classes]
