from django.test import TestCase
from django.db.models import Prefetch

from api.v1.serializers.examples_serializers import ExampleForUserSerializer, ExamplePATCHSerializer, ExamplePOSTSerializer, UserExample, ExampleGeantGETSerializer, ExampleGeantPOSTSerializer

from users.models import User

from geant_examples.models import *

from rest_framework.exceptions import ErrorDetail


class ExampleForUserSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='test_username', email='test@gmail.com')
        example = Example.objects.create(title='test_ex')
        example.users.add(self.user)
        example.save()
        example_user = UserExample.objects.create(
            example=example, user=self.user)

    def test_get_status(self):
        queryset = Example.objects.filter(users__id=self.user.id).only('title').prefetch_related(
            Prefetch(
                'example_users',
                queryset=UserExample.objects.filter(
                    user=self.user.id).only('example', 'status'),
                to_attr='example_user'
            ),
            'tags'
        ).distinct()
        serializer = ExampleForUserSerializer(instance=queryset, many=True)

        self.assertEqual(serializer.data, [
                         {'title': 'test_ex', 'tags': [], 'status': 2}])


class ExamplePOSTSerializerTestCase(TestCase):
    def setUp(self):
        self.data = {
            "title": "test_verbose",
            "users": [
                {
                    "username": "test_username"
                }
            ],
            "category": "default"
        }
        User.objects.create(
            username=self.data['users'][0]['username'], email='test@gmail.com')
        self.example_title_rel = ExamplesTitleRelation.objects.create(
            title_verbose='test_verbose', title_not_verbose='TSU_XX_00')

    def test_create(self):
        data = self.data

        self.assertFalse(Example.objects.filter(title=self.data['title']))
        self.assertFalse(UserExample.objects.filter(
            example__title=data['title'], user__username=data['users'][0]['username']).exists())

        serializer = ExamplePOSTSerializer(data=data)
        serializer.is_valid()
        serializer.save()

        self.assertTrue(Example.objects.filter(title=self.data['title']))
        self.assertTrue(UserExample.objects.filter(
            example__title=data['title'], user__username=data['users'][0]['username']).exists())

    def test_validate(self):
        data = self.data
        serializer = ExamplePOSTSerializer(data=data)

        self.assertTrue(serializer.is_valid())

        data.update(
            {'users': [{'username': 'gashish'}, {'username': 'gashish'}]})
        serializer = ExamplePOSTSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'non_field_errors': [
                         ErrorDetail(string='Users must be unique', code='invalid')]})

        data.update({'users': [{'username': 'gashish'}]})
        serializer = ExamplePOSTSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'non_field_errors': [ErrorDetail(
            string='Any of given users do not exist', code='invalid')]})

        data = self.data
        data.update({'title': '', 'params': ''})
        serializer = ExamplePOSTSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'title': [ErrorDetail(
            string='This field may not be blank.', code='blank')]})

        data = self.data
        data.update({'title': 'bla'})
        serializer = ExamplePOSTSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'non_field_errors': [ErrorDetail(
            string='This title not in possible title list', code='invalid')]})


class ExamplePATCHSerializerTestCase(TestCase):
    def setUp(self):
        self.data = {
            'title': 'test_verbose',
            "users": [
                {
                    "username": "test_username"
                }
            ],
            "category": "default"
        }
        User.objects.create(
            username=self.data['users'][0]['username'], email='test@gmail.com')
        self.example_title_rel = ExamplesTitleRelation.objects.create(
            title_verbose='test_verbose', title_not_verbose='TSU_XX_00')

    def test_update(self):
        serializer = ExamplePOSTSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        new_user = User.objects.create(
            username='test_username2', email='test_2@gmail.com')
        data_to_update = {
            'users': [
                {
                    'username': 'test_username2'
                }
            ],
        }

        self.assertFalse(UserExample.objects.filter(user=new_user).exists())
        self.assertTrue(UserExample.objects.filter(
            user__username='test_username').exists())

        example = Example.objects.get(title=self.data['title'])
        serializer = ExamplePATCHSerializer(
            instance=example, data=data_to_update)
        serializer.is_valid()
        serializer.save()
        self.assertTrue(UserExample.objects.filter(user=new_user).exists())
        self.assertTrue(UserExample.objects.filter(
            user__username='test_username').exists())


class ExampleGeantPOSTSerializerTestCase(TestCase):
    def setUp(self):
        self.example_title_rel = ExamplesTitleRelation.objects.create(
            title_verbose='test_verbose', title_not_verbose='TSU_XX_00')
        self.example = Example.objects.create(title='test_verbose')
        self.data = {
            'params': 'key-s3_velocity_333'
        }

    def test_validate(self):
        data = self.data

        serializer = ExampleGeantPOSTSerializer(
            data=data, context={'example_pk': self.example.id})
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertTrue(ExampleGeant.objects.filter(
            title=self.example_title_rel.title_not_verbose, example=self.example, key_s3=data['params']).exists())

        data = self.data
        serializer = ExampleGeantPOSTSerializer(
            data=data, context={'example_pk': 12123})
        self.assertFalse(serializer.is_valid())
