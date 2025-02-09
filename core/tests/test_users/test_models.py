from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist

from users.models import User
from django.test import TestCase
from django.utils.translation import gettext_lazy as _


class UserTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@gmail.com',
            password='test_password',
            username='test_username',
        )

    def test_str_method(self):
        self.assertEqual(self.user.__str__(), self.user.tag)

    def test_verbose_name(self):
        self.assertEqual(self.user._meta.verbose_name, _("User"))
        self.assertEqual(self.user._meta.verbose_name_plural, _("Users"))

    def test_add_employee_in_employee_group(self):
        self.user.is_employee = True
        self.user.save()

        employee_group, created = Group.objects.get_or_create(name="Employees")
        self.assertIn(employee_group, self.user.groups.all())

    def test_add_employee_in_employee_group_does_not_exist(self):
        self.user.is_employee = True
        self.user.save()

        with self.assertRaises(ObjectDoesNotExist):
            Group.objects.get(name="NonExistingGroup")
