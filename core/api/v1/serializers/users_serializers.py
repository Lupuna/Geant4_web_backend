from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from users.models import User


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', )


class UserProfileCommonUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', )
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }


class UserQuickInfoSerializer(serializers.Serializer):
    username = serializers.CharField()


class LoginUpdateSerializer(serializers.Serializer):
    new_username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        user = self.instance

        if not user.check_password(attrs.get('password')):
            raise ValidationError('Given wrong password')

        attrs.pop('password')

        new_username = attrs.get('new_username')

        if User.objects.filter(username=new_username).exists():
            raise ValidationError('User with this username already exists')

        attrs = {'username': new_username}

        return attrs

    def update(self, instance, validated_data):
        instance.username = validated_data['username']
        instance.save()

        return instance


class PasswordUpdateSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        new_password2 = attrs.get('new_password2')

        if new_password != new_password2:
            raise ValidationError('Password do not match')

        attrs.pop('new_password2')

        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()

        return instance


class UserEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise ValidationError('User with this email does not exist')

        return value
