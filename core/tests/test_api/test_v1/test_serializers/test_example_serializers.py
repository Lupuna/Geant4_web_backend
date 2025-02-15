from django.test import TestCase
from django.db.models import Prefetch

from api.v1.serializers.examples_serializers import ExampleForUserSerializer, ExamplePATCHSerializer, ExamplePOSTSerializer, UserExample

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
            "title": "test_ex",
            "params": 'safsfa',
            "users": [
                {
                    "username": "test_username"
                }
            ],
            "category": "default"
        }
        User.objects.create(
            username=self.data['users'][0]['username'], email='test@gmail.com')

    def test_create(self):
        data = self.data

        self.assertFalse(Example.objects.filter(key_s3=self.data['params']))
        self.assertFalse(UserExample.objects.filter(
            example__title=data['title'], user__username=data['users'][0]['username']).exists())

        serializer = ExamplePOSTSerializer(data=data)
        serializer.is_valid()
        serializer.save()

        self.assertTrue(Example.objects.filter(key_s3=self.data['params']))
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
        self.assertEqual(serializer.errors, {'title': [ErrorDetail(string='This field may not be blank.', code='blank')], 'params': [
                         ErrorDetail(string='This field may not be blank.', code='blank')]})


class ExamplePATCHSerializerTestCAse(TestCase):
    def setUp(self):
        self.data = {
            "title": "test_ex",
            "params": 'safsfa',
            "users": [
                {
                    "username": "test_username"
                }
            ],
            "category": "default"
        }
        User.objects.create(
            username=self.data['users'][0]['username'], email='test@gmail.com')

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

        example = Example.objects.get(key_s3=self.data['params'])
        serializer = ExamplePATCHSerializer(
            instance=example, data=data_to_update)
        serializer.is_valid()
        serializer.save()
        self.assertTrue(UserExample.objects.filter(user=new_user).exists())
        self.assertTrue(UserExample.objects.filter(
            user__username='test_username').exists())
