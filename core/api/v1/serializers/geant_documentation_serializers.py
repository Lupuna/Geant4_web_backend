from django.db import transaction
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.reverse import reverse_lazy

from geant_documentation.models import Article, Category, Chapter, Element, File, Subscription


class RealFileSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)


class FileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ('id', 'uuid', 'format', 'url')
        read_only_fields = ('id', 'uuid')

    def get_url(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        return request.build_absolute_uri(
            reverse_lazy('file-manage', kwargs={'uuid': obj.uuid, 'file_format': obj.format})
        )


class ElementSerializer(WritableNestedModelSerializer):
    files = FileSerializer(many=True)


    class Meta:
        model = Element
        fields = ('id', 'text', 'element_order', 'type', 'files')

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)

        return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.files.all().delete()
            instance = super().update(instance, validated_data)

        return instance


class SubscriptionSerializer(WritableNestedModelSerializer):
    elements = ElementSerializer(many=True)

    class Meta:
        model = Subscription
        fields = ('id', 'title', 'subscription_order', 'elements')

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)

        return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.elements.all().delete()
            instance = super().update(instance, validated_data)

        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = '__all__'


class ArticleListSerializer(serializers.ModelSerializer):
    chapter = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ('id', 'category', 'chapter', 'description', 'title', 'chosen')

    def get_category(self, obj):
        return obj.category.title if obj.chapter else None

    def get_chapter(self, obj):
        return obj.chapter.title if obj.chapter else None


class ArticleSerializer(WritableNestedModelSerializer):
    chapter = serializers.PrimaryKeyRelatedField(queryset=Chapter.objects.all(), required=False, allow_null=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    subscriptions = SubscriptionSerializer(many=True)

    class Meta:
        model = Article
        fields = '__all__'

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)

        return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.subscriptions.all().delete()
            instance = super().update(instance, validated_data)

        return instance
