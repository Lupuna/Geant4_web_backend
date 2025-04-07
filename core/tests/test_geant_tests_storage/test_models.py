from django.test import TestCase
from geant_tests_storage.models import Version, TestResult, TestResultFile, FileModeModel
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta


class VersionTestCase(TestCase):

    def setUp(self):
        self.version = Version.objects.create(
            title='test_version_1'
        )

    def test_str_method(self):
        self.assertEqual(self.version.__str__(), self.version.title)

    def test_verbose_name(self):
        self.assertEqual(self.version._meta.verbose_name, _("Version"))
        self.assertEqual(self.version._meta.verbose_name_plural, _("Versions"))


class TestResultTestCase(TestCase):

    def setUp(self):
        self.version = Version.objects.create(
            title='test_version_1'
        )
        self.test_result = TestResult.objects.create(
            title='test_result_1',
            version=self.version
        )

    def test_str_method(self):
        self.assertEqual(self.test_result.__str__(), self.test_result.title)

    def test_verbose_name(self):
        self.assertEqual(self.test_result._meta.verbose_name, _("TestResult"))
        self.assertEqual(
            self.test_result._meta.verbose_name_plural, _("TestsResults"))

    def test_date_to_delete_validator_raise_create_exception(self):
        test_result = TestResult(
            title='test_result_1',
            version=self.version,
            creation_date=datetime.now(),
            day_to_delete=datetime.now() - timedelta(days=30)
        )

        with self.assertRaises(ValueError) as context:
            test_result.date_to_delete_validator()

        self.assertEqual(
            str(context.exception),
            'The "day_to_delete" field must be later than "creation_date".'
        )

    def test_date_to_delete_validator_raise_update_exception(self):
        test_result = TestResult(
            title='test_result_1',
            version=self.version,
            date_to_update=datetime.now(),
            creation_date=datetime.now() - timedelta(days=30),
            day_to_delete=datetime.now() - timedelta(days=30)
        )

        with self.assertRaises(ValueError) as context:
            test_result.date_to_delete_validator()

        self.assertEqual(
            str(context.exception),
            'The "day_to_delete" field must be later than "date_to_update".'
        )


class TestResultFileTestCase(TestCase):

    def setUp(self):
        self.version = Version.objects.create(
            title='test_version_1'
        )
        self.test_result = TestResult.objects.create(
            title='test_result_1',
            version=self.version
        )
        self.file = TestResultFile.objects.create(
            test_result=self.test_result
        )

    def test_str_method(self):
        self.assertEqual(self.file.__str__(), str(self.file.uuid))

    def test_verbose_name(self):
        self.assertEqual(self.file._meta.verbose_name, _("TestResultFile"))
        self.assertEqual(self.file._meta.verbose_name_plural,
                         _("TestsResultsFiles"))


class FileModeModelTestCase(TestCase):
    def test_create(self):
        mode, created = FileModeModel.objects.get_or_create(mode=3)
        self.assertFalse(created)

        with self.assertRaises(ValueError):
            try_mode = FileModeModel.objects.create(mode=1)
