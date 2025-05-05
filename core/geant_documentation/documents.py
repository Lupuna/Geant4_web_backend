from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from geant_documentation.models import Article


@registry.register_document
class ArticleDocument(Document):
    class Index:
        name = 'articles'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': settings.ELASTICSEARCH_ANALYZER_SETTINGS
        }

    title = fields.TextField(
        analyzer="edge_ngram_analyzer",
        fields={
            "english": fields.TextField(
                analyzer="english_analyzer"
            ),
            "russian": fields.TextField(
                analyzer="russian_analyzer"
            ),
        }
    )
    description = fields.TextField(
        analyzer="edge_ngram_analyzer",
        fields={
            "english": fields.TextField(
                analyzer="english_analyzer"
            ),
            "russian": fields.TextField(
                analyzer="russian_analyzer"
            ),
        }
    )

    category = fields.KeywordField(multi=True)
    chapter = fields.KeywordField()
    chosen = fields.KeywordField()

    class Django:
        model = Article

    def prepare_chosen(self, instance):
        return instance.chosen

    def prepare_category(self, instance):
        return instance.category.title if instance.category else ""

    def prepare_chapter(self, instance):
        return instance.chapter.title if instance.chapter else ""
