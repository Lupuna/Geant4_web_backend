from rest_framework import serializers


class FileDataSerializer(serializers.Serializer):
    filename = serializers.CharField()
