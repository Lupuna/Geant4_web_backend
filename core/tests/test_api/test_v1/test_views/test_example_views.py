from django.urls import reverse

from geant_examples.models import Example, ExampleGeant, ExamplesTitleRelation

from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest

from api.v1.serializers.examples_serializers import ExampleGeantPOSTSerializer


class ExampleGeantViewSetTestCase(AuthSettingsTest):
    def setUp(self):
        self.example_titles_rel = ExamplesTitleRelation.objects.create(
            title_verbose='test_verbose', title_not_verbose='TSU_XX_00')
        self.example = Example.objects.create(title='test_verbose')

    def test_create(self):
        self.login_user()
        data = {
            'params': {
                'velocity': 144
            }
        }

        self.assertFalse(ExampleGeant.objects.filter(
            example=self.example, key_s3='key-s3_velocity_144').exists())
        response = self.client.post(reverse(
            'example-example-geant-list', kwargs={'example_pk': self.example.id}), data=data, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(ExampleGeant.objects.filter(
            example=self.example, key_s3='key-s3_velocity_144').exists())
        self.assertEqual(response.data, {
                         'id': 1, 'title': self.example_titles_rel.title_not_verbose, 'key_s3': 'key-s3_velocity_144'})
