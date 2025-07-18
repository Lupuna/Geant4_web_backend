from django.db import transaction
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse_lazy

from api.v1.serializers.utils import get_custom_absolute_uri
from geant_documentation.models import Article, Category, Chapter, Element, File, Subscription, ArticleUser


class RealFileSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)


class FileSerializer(WritableNestedModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ('id', 'uuid', 'format', 'url')
        read_only_fields = ('id',)
        extra_kwargs = {'uuid': {'required': False}}

    def get_url(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        return get_custom_absolute_uri(
            request,
            reverse_lazy('file-manage', kwargs={'uuid': obj.uuid, 'file_format': obj.format})
        )


class ElementSerializer(WritableNestedModelSerializer):
    files = FileSerializer(many=True)

    class Meta:
        model = Element
        fields = ('id', 'text', 'element_order', 'type', 'files')
        extra_kwargs = {'id': {'required': False}}

    def create(self, validated_data):
        with transaction.atomic():
            return super().create(validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            return super().update(instance, validated_data)


class SubscriptionSerializer(WritableNestedModelSerializer):
    elements = ElementSerializer(many=True)

    class Meta:
        model = Subscription
        fields = ('id', 'title', 'subscription_order', 'elements')
        extra_kwargs = {'id': {'required': False}}

    def create(self, validated_data):
        with transaction.atomic():
            return super().create(validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            return super().update(instance, validated_data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = '__all__'


class ArticleUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArticleUser
        fields = ('id', 'article')


class ArticleListSerializer(serializers.ModelSerializer):
    chapter = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ('id', 'category', 'chapter', 'description', 'title')

    def get_category(self, obj):
        return obj.category.title if obj.category else None

    def get_chapter(self, obj):
        return obj.chapter.title if obj.chapter else None


class ArticleSerializer(WritableNestedModelSerializer):
    chapter = serializers.PrimaryKeyRelatedField(queryset=Chapter.objects.all(), required=False, allow_null=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    subscriptions = SubscriptionSerializer(many=True)

    class Meta:
        model = Article
        fields = '__all__'
        extra_kwargs = {'id': {'required': False}}

    def create(self, validated_data):
        with transaction.atomic():
            return super().create(validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            return super().update(instance, validated_data)


class ArticleIdSerializer(serializers.ModelSerializer):

    class Meta:
        model = Article
        fields = ('id', )
