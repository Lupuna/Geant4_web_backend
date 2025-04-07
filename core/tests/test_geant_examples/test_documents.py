from unittest import TestCase
from django.conf import settings

from geant_examples.documents import ExampleDocument

class DocumentBaseTestCase(TestCase):
    def test_analysis_settings(self):
        self.assertEqual(
            settings.ELASTICSEARCH_ANALYZER_SETTINGS, ExampleDocument.Index.settings["analysis"]
        )
