from django.urls import reverse

from geant_examples.models import Example

from tests.test_api.test_v1.test_views.auth_test_base import AuthSettingsTest


class ExampleViewSetTestCase(AuthSettingsTest):
    def test_create_key_s3(self):
        data = {
            "title": "test_ex",
            "params": {
                'par1': 33
            },
            "category": "default"
        }
        self.login_user()
        self.assertFalse(Example.objects.filter(
            key_s3='key-s3_par1_33').exists())
        response = self.client.post(
            reverse('examples-list'), data=data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Example.objects.filter(
            key_s3='key-s3_par1_33').exists())
