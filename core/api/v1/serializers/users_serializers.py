from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from users.models import User


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'tag', 'uuid', 'is_employee',
                  'is_staff', 'is_active', 'date_joined', 'first_name', 'last_name', )


class UserQuickInfoSerializer(serializers.Serializer):
    username = serializers.CharField()
