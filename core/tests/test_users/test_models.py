from users.models import User, Example, UserExample
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

    def test_generate_tag_method(self):
        with self.assertNumQueries(4):
            self.user.generate_tag()
        self.assertEqual(self.user.tag, f"{self.user.username}_{self.user.id+1}")


class ExampleTestCase(TestCase):

    def setUp(self):
        self.example = Example.objects.create(
            title='test_example_title_1',
            key_s3='test_key_s3_1',
        )

    def test_str_method(self):
        self.assertEqual(self.example.__str__(), self.example.title)

    def test_verbose_name(self):
        self.assertEqual(self.example._meta.verbose_name, _("Example"))
        self.assertEqual(self.example._meta.verbose_name_plural, _("Examples"))


class UserExampleTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@gmail.com',
            password='test_password',
            username='test_username',
        )
        self.example = Example.objects.create(
            title='test_example_title_1',
            key_s3='test_key_s3_1',
        )

        self.user_example = UserExample.objects.create(
            user=self.user,
            example=self.example
        )

    def test_str_method(self):
        self.assertEqual(self.user_example.__str__(), self.user_example.creation_date)

    def test_verbose_name(self):
        self.assertEqual(self.user_example._meta.verbose_name, _("UserExample"))
        self.assertEqual(self.user_example._meta.verbose_name_plural, _("UsersExamples"))

    def test_ordering(self):
        self.assertEqual(self.user_example._meta.ordering, ('user', 'creation_date'))
