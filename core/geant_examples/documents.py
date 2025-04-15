from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.conf import settings

from .models import Example


@registry.register_document
class ExampleDocument(Document):
    class Index:
        name = 'examples'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': settings.ELASTICSEARCH_ANALYZER_SETTINGS
        }

    title_verbose = fields.TextField(
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
    tags = fields.KeywordField(multi=True)
    category = fields.KeywordField()

    class Django:
        model = Example

    def prepare_tags(self, instance):
        return [tag.title for tag in instance.tags.all()]
