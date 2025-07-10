from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from geant_examples.models import UserExampleCommand


@registry.register_document
class UserExampleCommandDocument(Document):
    class Index:
        name = 'user_example_command'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': settings.ELASTICSEARCH_ANALYZER_SETTINGS
        }

    title_verbose = fields.TextField(
        analyzer="edge_ngram_analyzer",
        fields={
            "keyword": fields.KeywordField(),
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
    creation_date = fields.DateField()
    synchronized = fields.BooleanField()

    class Django:
        model = UserExampleCommand

    def prepare_title_verbose(self, instance):
        return instance.example_command.example.title_verbose

    def prepare_description(self, instance):
        return instance.example_command.example.description

    def prepare_tags(self, instance):
        return [tag.title for tag in instance.example_command.example.tags.all()]

    def prepare_category(self, instance):
        category = instance.example_command.example.category
        return category.title if category else None

    def prepare_date_to_update(self, instance):
        return instance.creation_date.isoformat()

    def prepare_synchronized(self, instance):
        return instance.example_command.example.synchronized
