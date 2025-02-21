from drf_spectacular.utils import extend_schema

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from file_client.tasks import download_file, update_file, upload_file, remove_file

from api.v1.serializers.files_serializers import FileDataSerializer


@extend_schema(
    tags=['Files endpoint']
)
class DownloadTemporaryFileAPIWiew(APIView):
    permission_classes = (IsAuthenticated, )

    @extend_schema(request=FileDataSerializer)
    def post(self, request, *args, **kwargs):
        serializer = FileDataSerializer(data=request.data)

        if serializer.is_valid():
            download_file.delay(serializer.data)

            return Response({'detail': 'Downloading started'}, status=status.HTTP_202_ACCEPTED)

        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Files endpoint']
)
class UploadTemporaryFileAPIView(APIView):
    permission_classes = (IsAuthenticated, )

    @extend_schema(request=FileDataSerializer)
    def post(self, request, *args, **kwargs):
        serializer = FileDataSerializer(data=request.data)

        if serializer.is_valid():
            upload_file.delay(serializer.data)

            return Response({'detail': 'File upload started'}, status=status.HTTP_202_ACCEPTED)

        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Files endpoint']
)
class UpdateTemporaryFileAPIView(APIView):
    permission_classes = (IsAuthenticated, )

    @extend_schema(request=FileDataSerializer)
    def post(self, request, *args, **kwargs):
        serializer = FileDataSerializer(data=request.data)

        if serializer.is_valid():
            update_file.delay(serializer.data)

            return Response({'detail': 'File update started'}, status=status.HTTP_202_ACCEPTED)

        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Files endpoint']
)
class RemoveTemporaryFileAPIView(APIView):
    permission_classes = (IsAuthenticated, )

    @extend_schema(request=FileDataSerializer)
    def post(self, request, *args, **kwargs):
        serializer = FileDataSerializer(data=request.data)

        if serializer.is_valid():
            remove_file.delay(serializer.data)

            return Response({'detail': 'File removed'}, status=status.HTTP_202_ACCEPTED)

        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
