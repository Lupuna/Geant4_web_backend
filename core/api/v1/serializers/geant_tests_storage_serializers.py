from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from geant_tests_storage.models import Version, TestResult, TestResultFile


class VersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Version
        fields = ('id', 'title', 'day_to_delete', )


class TestResultFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestResultFile
        fields = ('id', 'uuid', 'day_to_delete', )


class TestResultSerializer(serializers.ModelSerializer):
    files = TestResultFileSerializer(many=True, read_only=True)

    class Meta:
        model = TestResult
        fields = (
            'id', 'title', 'version',
            'date_to_update', 'creation_date',
            'day_to_delete', 'files'
        )


class ModeSerializer(serializers.Serializer):
    mode = serializers.IntegerField(required=True)

    def validate(self, attrs):
        mode = attrs.get('mode')

        if not mode in (1, 2, 3, ):
            raise ValidationError('Mode can take values only 1, 2 or 3')

        return attrs

    def update(self, instance, validated_data):
        instance.mode = validated_data['mode']
        instance.save()

        return instance
