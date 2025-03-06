import shutil
import tempfile

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group, Permission

from rest_framework.test import APIClient

from users.models import User

from geant_tests_storage.models import FileModeModel


class AuthSettingsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.emp_group = Group.objects.get(name='Employees')
        cls.sub_emp = Group.objects.create(name='Sub')

        cls.user = User.objects.create_user(
            email='test_email1@gmail.com',
            username='test_username1',
            first_name='test_fname1',
            last_name='test_lname1'
        )
        cls.user.set_password('test_pas1')
        cls.user.save()

        cls.employee = User.objects.create_employee_user(
            email='employee@gmail.com',
            username='employee',
            first_name='emp_fname',
            last_name='emp_lname',
            password='emp_pas'
        )

        cls.staff = User.objects.create_superuser(
            email='staff@gmail.com',
            username='staff',
            first_name='staff_fname',
            last_name='staff_lname'
        )
        cls.staff.set_password('staff_pas')
        cls.staff.save()

        cls.client = APIClient()

    def login_user(self):
        data = {'username': self.user.username, 'password': 'test_pas1'}
        self.client.post(reverse('login'), data=data)

    def logout(self):
        self.client.post(reverse('logout'))

    def login_employee(self):
        self.client.post(reverse('login'), data={
            'username': self.employee.username, 'password': 'emp_pas'})

    def login_staff(self):
        self.client.post(reverse('login'), data={
            'username': self.staff.username, 'password': 'staff_pas'})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
