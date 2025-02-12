from django.test import TestCase

from geant_examples.models import Example, UserExample, Tag
from users.models import User
from django.utils.translation import gettext_lazy as _


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
        self.assertEqual(self.user_example.__str__(),
                         str(self.user_example.creation_date))

    def test_verbose_name(self):
        self.assertEqual(self.user_example._meta.verbose_name,
                         _("UserExample"))
        self.assertEqual(
            self.user_example._meta.verbose_name_plural, _("UsersExamples"))

    def test_ordering(self):
        self.assertEqual(self.user_example._meta.ordering,
                         ('user', 'creation_date'))


class TagTestCase(TestCase):

    def setUp(self):
        self.tag = Tag.objects.create(
            title='test_tag_title_1'
        )

    def test_str_method(self):
        self.assertEqual(self.tag.__str__(), self.tag.title)

    def test_verbose_name(self):
        self.assertEqual(self.tag._meta.verbose_name, _("Tag"))
        self.assertEqual(self.tag._meta.verbose_name_plural, _("Tags"))
