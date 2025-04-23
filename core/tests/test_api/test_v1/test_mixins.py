from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.exceptions import ValidationError as DRFValidationError

from api.v1.views.mixins import ValidationHandlingMixin


class ValidationHandlingMixinTests(TestCase):
    def setUp(self):
        self.mixin = ValidationHandlingMixin()

    def test_perform_create_success(self):
        class DummySerializer:
            def save(self, **kwargs):
                return 'created'

        serializer = DummySerializer()
        result = self.mixin.perform_create(serializer)
        self.assertEqual(result, 'created')

    def test_perform_create_django_validation_error(self):
        class DummySerializer:
            def save(self, **kwargs):
                raise DjangoValidationError("some error")

        serializer = DummySerializer()
        with self.assertRaises(DRFValidationError) as exc:
            self.mixin.perform_create(serializer)
        self.assertIn("some error", str(exc.exception))

    def test_perform_create_integrity_error(self):
        class DummySerializer:
            def save(self, **kwargs):
                raise IntegrityError("integrity issue")

        serializer = DummySerializer()
        with self.assertRaises(DRFValidationError) as exc:
            self.mixin.perform_create(serializer)
        self.assertIn("integrity issue", str(exc.exception))

    def test_perform_update_success(self):
        class DummySerializer:
            def save(self, **kwargs):
                return 'updated'

        serializer = DummySerializer()
        result = self.mixin.perform_update(serializer)
        self.assertEqual(result, 'updated')

    def test_perform_update_django_validation_error(self):
        class DummySerializer:
            def save(self, **kwargs):
                raise DjangoValidationError("update error")

        serializer = DummySerializer()
        with self.assertRaises(DRFValidationError) as exc:
            self.mixin.perform_update(serializer)
        self.assertIn("update error", str(exc.exception))

    def test_perform_update_integrity_error(self):
        class DummySerializer:
            def save(self, **kwargs):
                raise IntegrityError("update integrity issue")

        serializer = DummySerializer()
        with self.assertRaises(DRFValidationError) as exc:
            self.mixin.perform_update(serializer)
        self.assertIn("update integrity issue", str(exc.exception))
