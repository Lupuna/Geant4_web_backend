from .users_serializers import UserQuickInfoSerializer

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.v1.serializers.validators import m2m_validator

from django.contrib.auth.models import Group, Permission

from users.models import User


class PermissionQuickInfoSerializer(serializers.Serializer):
    codename = serializers.CharField()


class BaseGroupSerializer(serializers.Serializer):
    def validate_name(self, value):
        return value

    def validate_user_set(self, value):
        return m2m_validator(value, User, 'username')

    def validate_permissions(self, value):
        return m2m_validator(value, Permission, 'codename')

    def create(self, validated_data):
        return super().create(validated_data)

    def update_objs(self, instance, validated_data) -> None:
        return None

    def delete_objs(self, instance, validated_data) -> dict:
        return {}

    def save(self, **kwargs):
        return super().save(**kwargs)


class GroupPATCHSerializer(BaseGroupSerializer):
    user_set = UserQuickInfoSerializer(many=True, required=False)
    permissions = PermissionQuickInfoSerializer(many=True, required=False)

    def delete_objs(self, instance, validated_data):
        delete_info = {}

        for field, data in validated_data.items():
            objs = getattr(instance, field)
            identificator = list(data[0].keys())[0]
            values_to_delete = tuple(map(lambda x: x[identificator], data))
            objs_to_delete = objs.filter(
                **{f'{identificator}__in': values_to_delete})
            objs.remove(*objs_to_delete)
            delete_info[f'Deleted {identificator}s'] = values_to_delete

        return delete_info

    def update_objs(self, instance, validated_data):
        for field, data in validated_data.items():
            objs = getattr(instance, field)
            identificator = list(data[0].keys())[0]
            values_to_add = tuple(map(lambda x: x[identificator], data))
            objs_to_add = objs.model.objects.filter(
                **{f'{identificator}__in': values_to_add})
            objs.add(*objs_to_add)

    def save(self, **kwargs):
        delete = self.context.get('delete', False)

        if delete:
            return self.delete_objs(self.instance, self.validated_data)
        else:
            self.update_objs(self.instance, self.validated_data)


class GroupPOSTSerializer(BaseGroupSerializer):
    name = serializers.CharField(required=True)
    user_set = UserQuickInfoSerializer(many=True, required=False)
    permissions = PermissionQuickInfoSerializer(many=True, required=False)

    def validate_name(self, value):
        if Group.objects.filter(name=value).exists():
            raise ValidationError('Group already exists')
        return value

    def create(self, validated_data):
        group = Group.objects.create(name=validated_data['name'])
        del validated_data['name']
        GroupPATCHSerializer.update_objs(self, group, validated_data)

    def save(self, **kwargs):
        self.create(self.validated_data)
