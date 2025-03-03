from drf_spectacular.utils import extend_schema

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from file_client.tasks import download_file, update_file, upload_file, remove_file

from api.v1.serializers.files_serializers import FileDataSerializer


class FileBaseAPIView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        serializer = FileDataSerializer(data=request.data)

        if serializer.is_valid():
            return Response({'detail': 'Process started'}, status=status.HTTP_202_ACCEPTED), serializer.data

        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST), {}


@extend_schema(
    tags=['Files endpoint'],
    request=FileDataSerializer
)
class DownloadTemporaryFileAPIWiew(FileBaseAPIView):
    def post(self, request, *args, **kwargs):
        response, validated_data = super().post(request, *args, **kwargs)

        if validated_data:
            download_file.delay(validated_data)

            return response

        return response


@extend_schema(
    tags=['Files endpoint'],
    request=FileDataSerializer
)
class UploadTemporaryFileAPIView(FileBaseAPIView):
    def post(self, request, *args, **kwargs):
        response, validated_data = super().post(request, *args, **kwargs)

        if validated_data:
            upload_file.delay(validated_data)

            return response

        return response


@extend_schema(
    tags=['Files endpoint'],
    request=FileDataSerializer
)
class UpdateTemporaryFileAPIView(FileBaseAPIView):
    def post(self, request, *args, **kwargs):
        response, validated_data = super().post(request, *args, **kwargs)

        if validated_data:
            update_file.delay(validated_data)

            return response

        return response


@extend_schema(
    tags=['Files endpoint'],
    request=FileDataSerializer
)
class RemoveTemporaryFileAPIView(FileBaseAPIView):
    def post(self, request, *args, **kwargs):
        response, validated_data = super().post(request, *args, **kwargs)

        if validated_data:
            remove_file.delay(validated_data)

            return response

        return response
