from .users_serializers import UserQuickInfoSerializer

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.v1.serializers.validators import m2m_add_validators

from django.contrib.auth.models import Group

from users.models import User


class LimitedEmployeeGroupDELETESerializer(serializers.Serializer):
    users = UserQuickInfoSerializer(many=True, required=True)

    def validate(self, attrs):
        users_data = attrs.get('users')
        usernames_to_delete = m2m_add_validators(users_data, User, 'username')
        in_limited_group = Group.objects.filter(name='LimitedEmployeeGroup').first(
        ).user_set.filter(username__in=usernames_to_delete).values_list('username', flat=True)

        if len(usernames_to_delete) != len(in_limited_group):
            not_in_limited_group = set(
                usernames_to_delete) - set(in_limited_group)

            raise ValidationError(
                f'Theese users: ({', '.join(not_in_limited_group)}) - are not in LimitedEmployeeGroup')

        return attrs

    def delete(self, instance, validated_data):
        usernames_to_delete = [user_data['username']
                               for user_data in validated_data['users']]
        users_to_delete = instance.user_set.filter(
            username__in=usernames_to_delete)
        instance.user_set.remove(*users_to_delete)

        return usernames_to_delete


class LimitedEmployeeGroupPATCHSerializer(serializers.Serializer):
    users = UserQuickInfoSerializer(many=True)

    def validate(self, attrs):
        users_data = attrs.get('users')

        if users_data:
            usernames = m2m_add_validators(
                users_data, User, identificator='username')
            employee_group = Group.objects.filter(
                name='Employees').first()
            employees_usrnames_set = set(employee_group.user_set.filter(
                username__in=usernames).values_list('username', flat=True))

            if len(usernames) != len(employees_usrnames_set):
                not_employees = set(usernames) - employees_usrnames_set

                raise ValidationError(
                    f'Theese users: ({', '.join(not_employees)}) - are not Employees')

        return attrs

    def update(self, instance, validated_data):
        users_data = validated_data['users']
        usernames = [user_data['username'] for user_data in users_data]
        users_to_add = User.objects.filter(username__in=usernames)

        instance.user_set.add(*users_to_add)

        return usernames
