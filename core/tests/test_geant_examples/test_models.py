from django.test import TestCase

from geant_examples.models import Example, UserExample, Tag, ExampleGeant, ExamplesTitleRelation
from users.models import User
from django.utils.translation import gettext_lazy as _


class ExampleTestCase(TestCase):

    def setUp(self):
        self.example_title_rel = ExamplesTitleRelation.objects.create(
            title_verbose='test_verbose', title_not_verbose='TSU_XX_00')
        self.example = Example.objects.create(
            title='test_verbose'
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
            title='test_verbose',
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


class ExampleGeantTestCase(TestCase):
    def setUp(self):
        self.example_title_rel = ExamplesTitleRelation.objects.create(
            title_verbose='test_verbose', title_not_verbose='TSU_XX_00')
        self.example = Example.objects.create(
            title='test_verbose'
        )
        self.example_geant = ExampleGeant.objects.create(
            title=self.example_title_rel.title_not_verbose, key_s3='key-s3_velocity_666', example=self.example)

    def test_str(self):
        self.assertEqual(self.example_geant.__str__(),
                         self.example_geant.key_s3)

    def test_verbose_name(self):
        self.assertEqual(
            self.example_geant._meta.verbose_name, _("ExampleGeant"))
        self.assertEqual(
            self.example_geant._meta.verbose_name_plural, _("ExamplesGeant"))


class ExamplesTitleRelationTestcase(TestCase):
    def setUp(self):
        self.example_title_rel = ExamplesTitleRelation.objects.create(
            title_verbose='test_verbose', title_not_verbose='TSU_XX_00')

    def test_str(self):
        self.assertEqual(self.example_title_rel.__str__(),
                         self.example_title_rel.title_verbose)

    def test_verbose_name(self):
        self.assertEqual(self.example_title_rel._meta.verbose_name, _(
            "Possible meanings of Examples titles"))
        self.assertEqual(self.example_title_rel._meta.verbose_name_plural, _(
            "Possible meanings of Examples titles"))

    def test_ordering(self):
        self.assertEqual(self.example_title_rel._meta.ordering,
                         ('title_not_verbose', ))
