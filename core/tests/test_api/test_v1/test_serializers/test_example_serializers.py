import datetime

from django.test import TestCase
from django.db.models import Prefetch
from django.forms.models import model_to_dict

from api.v1.serializers.examples_serializers import (
    ExampleForUserSerializer,
    ExamplePATCHSerializer,
    ExamplePOSTSerializer,
    UserExampleCommand,
    ExampleCommandGETSerializer,
    ExampleCommandPOSTSerializer
)

from users.models import User

from geant_examples.models import *

from rest_framework.exceptions import ErrorDetail


class ExampleForUserSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='test_username', email='test@gmail.com')
        self.example = Example.objects.create(
            title_verbose='test_ex', title_not_verbose='TSU_XX_00')
        self.ex_command = ExampleCommand.objects.create(
            example=self.example, key_s3='key-s3_v_11')
        self.ex_command.users.add(self.user)

    def test_get_data(self):
        user_ex_command = UserExampleCommand.objects.filter(
            user=self.user).prefetch_related('example_command__example').first()
        serializer = ExampleForUserSerializer(instance=user_ex_command)
        self.assertEqual(serializer.data, {'title_verbose': 'test_ex', 'description': '', 'creation_date': str(user_ex_command.creation_date)[:-6].replace(' ', 'T') + 'Z',
                         'date_to_update': self.example.date_to_update, 'status': 0, 'params': {'v': '11'}})


class ExamplePOSTSerializerTestCase(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(title='test_tag')
        self.data = {
            "title_verbose": "test_verbose",
            'title_not_verbose': 'TSU_XX_00',
            'tags': [
                {
                    'title': self.tag.title
                }
            ],
            "category": "default"
        }

    def test_create(self):
        data = self.data

        self.assertFalse(Example.objects.filter(
            title_verbose=self.data['title_verbose']))

        serializer = ExamplePOSTSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertTrue(Example.objects.filter(
            title_verbose=self.data['title_verbose']))
        self.assertTrue(Example.objects.get(
            title_verbose=self.data['title_verbose']).tags.filter(title=self.tag.title).exists())

    def test_validate(self):
        data = self.data
        serializer = ExamplePOSTSerializer(data=data)

        self.assertTrue(serializer.is_valid())

        data = self.data
        data.update({'tags': [{'title': 'any'}]})
        serializer = ExamplePOSTSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'tags': [ErrorDetail(
            string='Theese titles: (any) - do not exist', code='invalid')]})


class ExamplePATCHSerializerTestCase(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(title='test_tag')
        self.data = {
            "title_verbose": "test_verbose",
            'title_not_verbose': 'TSU_XX_00',
            "category": "default"
        }

    def test_update(self):
        serializer = ExamplePOSTSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        example = serializer.save()
        data_to_update = {
            'tags': [
                {
                    'title': self.tag.title
                }
            ],
        }

        self.assertFalse(Example.objects.filter(
            tags=self.tag).exists())
        serializer = ExamplePATCHSerializer(
            instance=example, data=data_to_update)
        serializer.is_valid()
        serializer.save()
        self.assertTrue(Example.objects.filter(
            tags=self.tag).exists())


class ExampleCommandPOSTSerializerTestCase(TestCase):
    def setUp(self):
        self.example = Example.objects.create(title_verbose='test_verbose')
        self.user = User.objects.create(
            username='test_username', email='test@gmail.com')
        self.data = {
            'params': 'key-s3_velocity_333'
        }

    def test_create_(self):
        self.assertFalse(ExampleCommand.objects.filter(
            users=self.user, example=self.example, key_s3=self.data['params']).exists())
        serializer = ExampleCommandPOSTSerializer(
            data=self.data, context={'example_pk': self.example.id, 'user': self.user})
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertTrue(ExampleCommand.objects.filter(
            users=self.user, example=self.example, key_s3=self.data['params']).exists())

    def test_validate(self):
        data = self.data

        self.assertFalse(ExampleCommand.objects.filter(
            users=self.user, example=self.example, key_s3=data['params']).exists())
        serializer = ExampleCommandPOSTSerializer(
            data=data, context={'example_pk': self.example.id, 'user': self.user})
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertTrue(ExampleCommand.objects.filter(
            users=self.user, example=self.example, key_s3=data['params']).exists())

        data = self.data
        serializer = ExampleCommandPOSTSerializer(
            data=data, context={'example_pk': 1223})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'non_field_errors': [ErrorDetail(
            string='Provided Example does not exists', code='invalid')]})

        serializer = ExampleCommandPOSTSerializer(
            data=data, context={'example_pk': self.example.id})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'non_field_errors': [ErrorDetail(
            string='ExampleCommand cannot be unattached to the user', code='invalid')]})
