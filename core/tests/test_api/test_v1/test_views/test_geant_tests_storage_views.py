from django.urls import reverse
from rest_framework.test import APIRequestFactory
from django.test import TestCase
from geant_tests_storage.models import Version, TestResult, TestResultFile
from api.v1.views.geant_tests_storage_views import TestResultAPIViewSet


class TestResultAPIViewSetTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.version = Version.objects.create(title="Version 1")
        self.another_version = Version.objects.create(title="Version 2")
        self.test_result1 = TestResult.objects.create(
            title="Test Result 1", version=self.version
        )
        self.test_result2 = TestResult.objects.create(
            title="Test Result 2", version=self.another_version
        )
        self.test_result_with_files = TestResult.objects.create(
            title="Test Result with Files", version=self.version
        )
        TestResultFile.objects.create(test_result=self.test_result_with_files)
        TestResultFile.objects.create(test_result=self.test_result_with_files)
        self.view = TestResultAPIViewSet()

    def test_get_queryset_for_get_request(self):
        kwargs = {'version_pk': self.version.id}
        url = reverse('version-test-result-list', kwargs=kwargs)
        request = self.factory.get(url)
        self.view.setup(request, **kwargs)

        expected_queryset = TestResult.objects.prefetch_related('files').filter(version=self.version.id)
        self.assertQuerySetEqual(self.view.get_queryset(), expected_queryset, ordered=False)

    def test_get_queryset_for_post_request(self):
        kwargs = {'version_pk': self.version.id}
        url = reverse('version-test-result-list', kwargs=kwargs)
        request = self.factory.post(url, {"title": "New Test Result"})
        self.view.setup(request, **kwargs)

        expected_queryset = TestResult.objects.filter(version=self.version.id)
        self.assertQuerySetEqual(self.view.get_queryset(), expected_queryset, ordered=False)
