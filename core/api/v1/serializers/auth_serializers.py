from users.models import User
from users.auth.validators import check_passwords_match

from rest_framework import serializers


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name',
                  'last_name', 'password', 'password2')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, data):
        password = data.get('password', None)
        password2 = data.get('password2', None)
        username = data.get('username', None)
        email = data.get('email', None)

        if not check_passwords_match(password, password2):
            raise serializers.ValidationError('Passwords do not match')
        data.pop('password2')

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'User with this username already exists')

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'User with this email already exists')

        return data

    def create(self, validated_data):
        user = User(email=validated_data['email'], username=validated_data['username'],
                    first_name=validated_data['first_name'], last_name=validated_data['last_name'])
        user.set_password(validated_data['password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    remember_me = serializers.BooleanField(default=False)
