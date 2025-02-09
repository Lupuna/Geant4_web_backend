import shutil
import tempfile

from django.conf import settings
from django.test import TestCase

from rest_framework.test import APIClient

from users.models import User


class AuthSettingsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.user = User.objects.create_user(
            email='test_email1@gmail.com',
            username='test_username1',
            first_name='test_fname1',
            last_name='test_lname1'
        )
        cls.user.set_password('test_pas1')
        cls.user.save()

        cls.client = APIClient()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
