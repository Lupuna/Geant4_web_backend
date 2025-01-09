from rest_framework import serializers
from geant_tests_storage.models import Version, TestResult, TestResultFile


class VersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Version
        fields = ('id', 'title')


class TestResultFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestResultFile
        fields = ('id', 'uuid')


class TestResultSerializer(serializers.ModelSerializer):
    files = TestResultFileSerializer(many=True, read_only=True)

    class Meta:
        model = TestResult
        fields = (
            'id', 'title', 'version',
            'date_to_update', 'creation_date',
            'day_to_delete', 'files'
        )


