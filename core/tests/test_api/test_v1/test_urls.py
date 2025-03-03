from django.test import SimpleTestCase
from django.urls import reverse, resolve

from api.v1.views.geant_tests_storage_views import TestResultAPIViewSet, VersionAPIViewSet


class VersionURLSTestCase(SimpleTestCase):
    def test_company_list_route(self):
        url = reverse('version-list')
        resolved_view = resolve(url).func.cls
        self.assertEqual(resolved_view, VersionAPIViewSet)

    def test_company_detail_route(self):
        url = reverse('version-detail', args=[1])
        resolved_view = resolve(url).func.cls
        self.assertEqual(resolved_view, VersionAPIViewSet)


class TestResultURLSTestCase(SimpleTestCase):
    def test_company_list_route(self):
        url = reverse('version-test-result-list', args=[1])
        resolved_view = resolve(url).func.cls
        self.assertEqual(resolved_view, TestResultAPIViewSet)

    def test_company_detail_route(self):
        url = reverse('version-test-result-detail', args=[1, 1])
        resolved_view = resolve(url).func.cls
        self.assertEqual(resolved_view, TestResultAPIViewSet)
