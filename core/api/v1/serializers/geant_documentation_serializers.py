from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from geant_documentation.models import Article, Category, Chapter, Element, File, Subscription


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ('id', 'uuid')


class ElementSerializer(WritableNestedModelSerializer):
    files = FileSerializer(many=True)

    class Meta:
        model = Element
        fields = '__all__'


class SubscriptionSerializer(WritableNestedModelSerializer):
    elements = ElementSerializer(many=True)

    class Meta:
        model = Subscription
        fields = '__all__'


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
    chapter = ChapterSerializer()
    category = CategorySerializer()
    subscriptions = SubscriptionSerializer(many=True)

    class Meta:
        model = Article
        fields = '__all__'
