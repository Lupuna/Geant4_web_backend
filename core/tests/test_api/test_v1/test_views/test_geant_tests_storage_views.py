from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ErrorDetail

from geant_tests_storage.models import Version, TestResult, TestResultFile, FileModeModel

from api.v1.views.geant_tests_storage_views import TestResultAPIViewSet, VersionAPIViewSet, FileModeAPIView

from .auth_test_base import AuthSettingsTest

from django.contrib.auth.models import Group, Permission


class TestResultAPIViewSetTestCase(AuthSettingsTest):
    def setUp(self):
        self.filemode, created = FileModeModel.objects.get_or_create(
            mode=3)
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

        expected_queryset = TestResult.objects.prefetch_related(
            'files').filter(version=self.version.id)
        self.assertQuerySetEqual(
            self.view.get_queryset(), expected_queryset, ordered=False)

    def test_get_queryset_for_post_request(self):
        kwargs = {'version_pk': self.version.id}
        url = reverse('version-test-result-list', kwargs=kwargs)
        request = self.factory.post(url, {"title": "New Test Result"})
        self.view.setup(request, **kwargs)

        expected_queryset = TestResult.objects.filter(version=self.version.id)
        self.assertQuerySetEqual(
            self.view.get_queryset(), expected_queryset, ordered=False)

    def test_permissions(self):
        self.login_user()
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, {'detail': ErrorDetail(
            string='Only employees can interact with TestResult or group(s) you are in has no permission for this action', code='permission_denied')})

        self.logout()
        self.login_employee()
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 200)

        self.logout()
        self.login_staff()
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 200)

        self.logout()
        self.filemode.mode = 2
        self.filemode.save()
        self.assertFalse(self.emp_group.permissions.all().exists())
        self.sub_emp.user_set.add(self.user)
        perm = Permission.objects.get(codename='view_testresult')
        self.sub_emp.permissions.add(perm)
        self.login_user()
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}), data={'any': 'data'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, {'detail': ErrorDetail(
            string='Only part of employees can interact with TestResult or group(s) you are in has no permission for this action', code='permission_denied')})

        self.logout()
        self.login_staff()
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 200)

        self.logout()
        self.login_employee()
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 403)
        self.sub_emp.user_set.add(self.employee)
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 200)

        self.logout()
        self.login_staff()
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 200)

        self.logout()
        self.filemode.mode = 1
        self.filemode.save()
        self.login_user()
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 403)
        self.logout()
        self.login_employee()
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 403)
        self.logout()
        self.login_staff()
        response = self.client.get(path=reverse(
            'version-test-result-list', kwargs={'version_pk': self.version.id}))
        self.assertEqual(response.status_code, 200)
