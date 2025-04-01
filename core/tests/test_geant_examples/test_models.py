from django.test import TestCase

from geant_examples.models import Example, UserExampleCommand, Tag, ExampleCommand
from users.models import User
from django.utils.translation import gettext_lazy as _


class ExampleTestCase(TestCase):

    def setUp(self):
        self.example = Example.objects.create(
            title_verbose='test_verbose',
            title_not_verbose='TSU_XX_00'
        )

    def test_str_method(self):
        self.assertEqual(self.example.__str__(),
                         self.example.title_not_verbose)

    def test_verbose_name(self):
        self.assertEqual(self.example._meta.verbose_name, _("Example"))
        self.assertEqual(self.example._meta.verbose_name_plural, _("Examples"))


class UserExampleCommandTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@gmail.com',
            password='test_password',
            username='test_username',
        )
        self.example = Example.objects.create(
            title_verbose='test_verbose',
            title_not_verbose='TSU_XX_00'
        )
        self.ex_command = ExampleCommand.objects.create(
            key_s3='key-s3_v_11', example=self.example)
        self.ex_command.users.add(self.user)
        self.us_ex_command = UserExampleCommand.objects.filter(
            user=self.user, example_command=self.ex_command).first()

    def test_str_method(self):
        self.assertEqual(self.us_ex_command.__str__(),
                         str(self.us_ex_command.creation_date) + f', status {self.us_ex_command.status}')

    def test_verbose_name(self):
        self.assertEqual(self.us_ex_command._meta.verbose_name,
                         _("UserExampleCommand"))
        self.assertEqual(
            self.us_ex_command._meta.verbose_name_plural, _("UsersExampleCommands"))

    def test_ordering(self):
        self.assertEqual(self.us_ex_command._meta.ordering,
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


class ExampleCommandTestCase(TestCase):
    def setUp(self):
        self.example = Example.objects.create(
            title_verbose='test_verbose',
            title_not_verbose='TSU_XX_00'
        )
        self.user = User.objects.create_user(
            email='admin@gmail.com',
            password='test_password',
            username='test_username',
        )
        self.example_command = ExampleCommand.objects.create(
            key_s3='key-s3_velocity_666', example=self.example)
        self.example_command.users.add(self.user)

    def test_str(self):
        self.assertEqual(self.example_command.__str__(),
                         self.example_command.key_s3)

    def test_verbose_name(self):
        self.assertEqual(
            self.example_command._meta.verbose_name, _("ExampleCommand"))
        self.assertEqual(
            self.example_command._meta.verbose_name_plural, _("ExampleCommands"))
