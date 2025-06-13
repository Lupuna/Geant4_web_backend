from django.http import FileResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from api.v1.serializers.geant_documentation_serializers import (
    ArticleListSerializer,
    ArticleSerializer,
    SubscriptionSerializer,
    ElementSerializer,
    ChapterSerializer,
    CategorySerializer, RealFileSerializer
)
from core.permissions import IsStaffPermission
from file_client.exceptions import FileClientException
from file_client.files_clients import ReadOnlyClient
from file_client.schema import file_schema
from file_client.tasks import (
    render_and_upload_documentation_image_task,
    render_and_update_documentation_graphic_task,
    render_and_upload_documentation_graphic_task,
    render_and_update_documentation_image_task
)
from file_client.utils import handle_file_upload
from geant_documentation.documents import ArticleDocument
from geant_documentation.models import Article, Subscription, Chapter, Category, Element
from .mixins import ElasticMixin, ValidationHandlingMixin


@extend_schema(
    tags=['Documentation Chapters']
)
class ChapterViewSet(ModelViewSet):
    serializer_class = ChapterSerializer
    queryset = Chapter.objects.all()

    @extend_schema(
        request=ChapterSerializer(many=True),
    )
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=201)

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        ids = request.data
        if ids is None:
            return Response({'detail': 'Incorrect id'}, status=status.HTTP_400_BAD_REQUEST)

        deleted_count, _ = Chapter.objects.filter(id__in=ids).delete()
        return Response({'deleted': deleted_count}, status=status.HTTP_204_NO_CONTENT)

    def perform_bulk_create(self, serializer):
        serializer.save()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsStaffPermission]
        return [permission() for permission in permission_classes]


@extend_schema(
    tags=['Documentation Categories']
)
class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    @extend_schema(
        request=CategorySerializer(many=True),
    )
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=201)

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        ids = request.data
        if ids is None:
            return Response({'detail': 'Incorrect id'}, status=status.HTTP_400_BAD_REQUEST)

        deleted_count, _ = Category.objects.filter(id__in=ids).delete()
        return Response({'deleted': deleted_count}, status=status.HTTP_204_NO_CONTENT)

    def perform_bulk_create(self, serializer):
        serializer.save()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsStaffPermission]
        return [permission() for permission in permission_classes]


@extend_schema(
    tags=['Documentation Files']
)
class FileViewSet(ViewSet):
    parser_classes = (MultiPartParser,)

    @classmethod
    def get_action_map(cls):
        return {
            'post': 'create',
            'patch': 'update',
            'get': 'retrieve',
            'delete': 'destroy'
        }

    @extend_schema(
        request=file_schema
    )
    def create(self, request, *args, **kwargs):
        serializer = RealFileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_path = handle_file_upload(
            serializer.validated_data.get('file'))

        uuid = str(kwargs['uuid'])
        match kwargs['file_format']:
            case 'webp':
                render_and_upload_documentation_image_task.delay(
                    old_path, uuid)
            case 'csv':
                render_and_upload_documentation_graphic_task.delay(
                    old_path, uuid)

        return Response({"detail": "Image processing started"}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        request=file_schema
    )
    def update(self, request, *args, **kwargs):
        serializer = RealFileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_path = handle_file_upload(
            serializer.validated_data.get('file'))
        uuid = str(kwargs['uuid'])
        match kwargs['file_format']:
            case 'webp':
                render_and_update_documentation_image_task.delay(
                    old_path, uuid)
            case 'csv':
                render_and_update_documentation_graphic_task.delay(
                    old_path, uuid)

        return Response({"detail": "Image processing started"}, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        uuid = str(kwargs['uuid'])
        ReadOnlyClient(name=uuid, file_format=kwargs['file_format']).delete()
        return Response({"detail": "Image deleted"}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        uuid = str(kwargs['uuid'])
        client = ReadOnlyClient(uuid, file_format=kwargs['file_format'])
        try:
            response = FileResponse(
                client.download(), as_attachment=True, filename=uuid + f'.{client.format}')
        except FileClientException as e:
            return Response(e.error, status=status.HTTP_404_NOT_FOUND)
        return response

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsStaffPermission]
        return [permission() for permission in permission_classes]


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
            elastic_document_class = self.get_elastic_document_class()
            self.setup_elastic_document_conf()
            search = elastic_document_class.search()
            result_search = self.elastic_full_query_handling(self.request, search)
            return result_search.to_queryset()
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

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        new_response_data = self.get_response_data_with_pages_count(response.data)
        response.data = new_response_data
        return response
