from users.models import User

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from django.test import TestCase

from api.v1.serializers.groups_serializers import GroupPATCHSerializer, GroupPOSTSerializer

from rest_framework.exceptions import ErrorDetail

from geant_examples.models import Example


class GroupPATCHSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_uname')
        self.example = Example.objects.create(
            title_verbose='test_verb', title_not_verbose='TSU_00')
        self.contype = ContentType.objects.get_for_model(Example)
        self.first_group = Group.objects.create(name='fgr')
        self.second_group = Group.objects.create(name='sgr')
        self.perm1 = Permission.objects.create(
            codename='add_smth', content_type=self.contype)
        self.perm2 = Permission.objects.create(
            codename='change_smth', content_type=self.contype)
        self.perm3 = Permission.objects.create(
            codename='view_smth', content_type=self.contype)
        self.data = {
            'user_set': [
                {
                    'username': self.user.username
                }
            ],
            'permissions': [
                {
                    'codename': self.perm1.codename
                }
            ]
        }

    def test_validate(self):
        data = self.data
        data.update(
            {
                'user_set': [
                    {
                        'username': self.user.username
                    },
                    {
                        'username': 'chauchau'
                    }
                ]
            }
        )

        serializer = GroupPATCHSerializer(instance=self.first_group, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'user_set': [ErrorDetail(
            string='Theese usernames: (chauchau) - do not exist', code='invalid')]})

        data = self.data
        data.update(
            {
                'user_set': [
                    {
                        'username': self.user.username
                    },
                    {
                        'username': self.user.username
                    }
                ]
            }
        )
        serializer = GroupPATCHSerializer(instance=self.first_group, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'user_set': [ErrorDetail(
            string='usernames must be unique', code='invalid')]})

        data = self.data
        data.update(
            {
                'user_set': [
                    {
                        'username': self.user.username
                    }
                ],
                'permissions': [
                    {
                        'codename': self.user.username
                    }
                ]
            }
        )
        serializer = GroupPATCHSerializer(instance=self.first_group, data=data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'permissions': [ErrorDetail(
            string='Theese codenames: (test_uname) - do not exist', code='invalid')]})

    def test_update(self):
        self.assertFalse(self.first_group.permissions.filter(
            codename=self.perm1.codename))
        self.assertFalse(self.first_group.user_set.filter(
            username=self.user.username))
        serializer = GroupPATCHSerializer(
            instance=self.first_group, data=self.data)

        self.assertTrue(serializer.is_valid())
        serializer.save()

        self.assertTrue(self.first_group.permissions.filter(
            codename=self.perm1.codename))
        self.assertTrue(self.first_group.user_set.filter(
            username=self.user.username))

    def test_delete(self):
        self.test_update()

        serializer = GroupPATCHSerializer(
            instance=self.first_group, data=self.data, context={'delete': True})
        serializer.is_valid()
        info = serializer.save()

        self.assertEqual(info, self.first_group)

        self.assertFalse(self.first_group.permissions.filter(
            codename=self.perm1.codename))
        self.assertFalse(self.first_group.user_set.filter(
            username=self.user.username))


class GroupPOSTSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_uname')
        self.example = Example.objects.create(
            title_verbose='test_verb', title_not_verbose='TSU_00')
        self.contype = ContentType.objects.get_for_model(Example)
        self.first_group = Group.objects.create(name='fgr')
        self.perm1 = Permission.objects.create(
            codename='add_smth', content_type=self.contype)
        self.perm2 = Permission.objects.create(
            codename='change_smth', content_type=self.contype)
        self.perm3 = Permission.objects.create(
            codename='view_smth', content_type=self.contype)
        self.data = {
            'name': 'test_gname',
            'user_set': [
                {
                    'username': self.user.username
                }
            ],
            'permissions': [
                {
                    'codename': self.perm1.codename
                }
            ]
        }

    def test_validate(self):
        data = self.data
        data.update({'name': self.first_group.name})

        serializer = GroupPOSTSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'name': [ErrorDetail(
            string='Group already exists', code='invalid')]})

    def test_create(self):
        self.assertFalse(Group.objects.filter(name=self.data['name']))

        serializer = GroupPOSTSerializer(data=self.data)

        self.assertTrue(serializer.is_valid())
        serializer.save()

        self.assertTrue(Group.objects.filter(name=self.data['name']).exists())
        group = Group.objects.filter(name='test_gname').first()

        self.assertTrue(group.permissions.filter(
            codename=self.perm1.codename).exists())
        self.assertTrue(group.user_set.filter(
            username=self.user.username).exists())
