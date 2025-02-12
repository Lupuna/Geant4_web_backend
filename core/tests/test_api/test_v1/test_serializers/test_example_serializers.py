from django.test import TestCase
from django.db.models import Prefetch

from api.v1.serializers.examples_serializers import ExampleForUserSerializer, ExampleSerializer, UserExample

from users.models import User

from geant_examples.models import *


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


class ExampleSerializerTestCase(TestCase):
    def setUp(self):
        self.data = {
            "title": "test_ex",
            "key_s3": "asxxssdzx",
            "users": [
                {
                    "username": "alijan"
                }
            ],
            "category": "default"
        }
        User.objects.create(
            username=self.data['users'][0]['username'], email='test@gmail.com')

    def test_create(self):
        data = self.data

        self.assertFalse(Example.objects.filter(key_s3=data['key_s3']))
        self.assertFalse(UserExample.objects.filter(
            example__title=data['title'], user__username=data['users'][0]['username']).exists())

        serializer = ExampleSerializer(data=data)
        serializer.is_valid()
        serializer.save()

        self.assertTrue(Example.objects.filter(key_s3=data['key_s3']))
        self.assertTrue(UserExample.objects.filter(
            example__title=data['title'], user__username=data['users'][0]['username']).exists())

    def test_create_fail(self):
        data = {
            "title": "test_ex",
            "key_s3": "asxxssdzx",
            "category": "default"
        }
        serializer = ExampleSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertFalse(Example.objects.filter(key_s3=data['key_s3']))
