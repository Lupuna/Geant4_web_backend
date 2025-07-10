from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.tasks import send_celery_mail
from users.auth.utils import make_disposable_url
from users.models import User
from .utils import raise_validation_error_instead_integrity


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name',
                  'last_name', 'is_staff')
        read_only_fields = ('is_staff',)


class UserUuidSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('uuid',)
        read_only_fields = ('uuid',)


class UserProfileImageSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)


class UserProfileCommonUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False, 'validators': []}
        }

    def validate_email(self, value):
        if value == self.instance.email:
            raise ValidationError('You already use this email')

        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise ValidationError('A user with this email already exists')

        return value

    def update(self, instance, validated_data):
        email = validated_data.pop('email', None)

        if email:
            url = make_disposable_url(settings.FRONTEND_URL + '/profile/update_email/',
                                      settings.EMAIL_UPDATE_SALT, {'new_email': email})
            message = f'Follow this link to confirm update your email on Geant4 service\n{url}'
            topic = 'Update email'
            send_celery_mail.delay(
                topic,
                message,
                [email]
            )

        return super().update(instance, validated_data)


class UserQuickInfoSerializer(serializers.Serializer):
    username = serializers.CharField()


class LoginUpdateSerializer(serializers.Serializer):
    new_username = serializers.CharField(required=True)

    @raise_validation_error_instead_integrity
    def update(self, instance, validated_data):
        instance.username = validated_data['new_username']
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


class PasswordProfileUpdateSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    old_password = serializers.CharField()

    def validate(self, attrs):
        old = attrs.pop('old_password')

        if not self.instance.check_password(old):
            raise ValidationError('Wrong current password')

        return attrs

    def update(self, instance, validated_data):
        return PasswordUpdateSerializer().update(instance, validated_data)
