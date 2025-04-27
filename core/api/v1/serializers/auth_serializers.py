from users.models import User
from users.auth.validators import check_passwords_match

from rest_framework import serializers

from .utils import obj_can_exist


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name',
                  'last_name', 'password', 'password2')
        extra_kwargs = {
            'email': {'required': True, 'validators': []},
            'username': {'required': True, 'validators': []},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, data):
        password = data.get('password', None)
        password2 = data.get('password2', None)

        if not check_passwords_match(password, password2):
            raise serializers.ValidationError('Passwords do not match')
        data.pop('password2')

        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.save()

        return user

    @obj_can_exist
    def save(self, **kwargs):
        return super().save(**kwargs)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    remember_me = serializers.BooleanField(default=False)