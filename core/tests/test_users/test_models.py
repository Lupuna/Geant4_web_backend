from users.models import User
from django.test import TestCase
from django.utils.translation import gettext_lazy as _


class TestUser(TestCase):

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



