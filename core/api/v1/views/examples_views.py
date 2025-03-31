import requests

from io import BytesIO

from file_client import download_url

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status

from api.v1.serializers.examples_serializers import (
    ExamplePOSTSerializer,
    ExampleGETSerializer,
    TagSerializer,
    ExamplePATCHSerializer,
    ExampleCommandGETSerializer,
    ExampleCommandPOSTSerializer,
    ExampleCommandUpdateStatusSerializer
)

from geant_examples.models import Example, Tag, UserExampleCommand, ExampleCommand

from drf_spectacular.utils import extend_schema

from django.conf import settings
from django.http import FileResponse

from cacheops import invalidate_model


@extend_schema(
    tags=['Example ViewSet']
)
class ExampleViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, )
    queryset = Example.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer(self, *args, **kwargs):
        match self.request.method:
            case 'GET':
                return ExampleGETSerializer(*args, **kwargs)
            case 'POST':
                return ExamplePOSTSerializer(*args, **kwargs)
            case 'PATCH':
                return ExamplePATCHSerializer(*args, **kwargs)


@extend_schema(
    tags=['ExampleCommand endpoint']
)
class ExampleCommandViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, )
    http_method_names = ['get', 'post', 'delete', ]

    def get_serializer(self, *args, **kwargs):
        if self.request.method in ['GET', ]:
            return ExampleCommandGETSerializer(*args, **kwargs)

        if self.request.method in ['POST', ]:
            kwargs.setdefault('context', self.get_serializer_context())
            return ExampleCommandPOSTSerializer(*args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {'example_pk': int(self.kwargs['example_pk']), 'user': self.request.user})

        return context

    def get_queryset(self):
        example = int(self.kwargs.get('example_pk'))

        return ExampleCommand.objects.filter(example=example)

    @extend_schema(request=ExampleCommandPOSTSerializer)
    def create(self, request, *args, **kwargs):
        params = request.data.get('params', {})
        user = request.user

        if params:
            str_params_vals = {str(key): str(val)
                               for key, val in params.items()}
            key_s3 = 'key-s3_' + '_'.join('_'.join(key_val)
                                          for key_val in str_params_vals.items())
            request.data['params'] = key_s3

            file_data = {'filename': key_s3 + '.zip'}
            download_from_storage = download_url
            example = Example.objects.get(
                id=self.kwargs.get('example_pk'))
            storage_response = requests.post(
                url=download_from_storage, data=file_data, json='json')

            if storage_response.status_code != 200:
                ex_commands = self.get_queryset().prefetch_related(
                    'example', 'users').filter(key_s3=key_s3)

                if not ex_commands.exists():
                    title_not_verbose = example.title_not_verbose
                    data = {
                        'title': title_not_verbose,
                        'commands': [
                            {param: str(val)} for param, val in params.items()
                        ]
                    }
                    url = settings.GEANT_BACKEND_RUN_EXAMPLE_URL
                    geant_response = requests.post(
                        url=url, data=data, json='json')

                    if geant_response.status_code == 200:
                        response = super().create(request, *args, **kwargs)

                        return response

                    return Response(data=geant_response.json(), status=geant_response.status_code, headers=geant_response.headers)

                ex_command = ex_commands.first()

                if not (user in ex_command.users.all()):
                    ex_command.users.add(user)

                return Response({'detail': 'Example already executed, wait for results'}, status=status.HTTP_200_OK)

            content_disposition = storage_response.headers.get(
                'Content-Disposition')
            filename = content_disposition.split(
                'filename=')[-1].strip('"')
            key_s3 = filename.split('.')[0]
            ex_command, created = ExampleCommand.objects.get_or_create(
                key_s3=key_s3, example=example)

            if not (user in ex_command.users.all()):
                ex_command.users.add(user)

            return FileResponse(BytesIO(storage_response.content), as_attachment=True, filename=filename)

        return Response({'error': 'You cannot start executing example without define paramrters'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['ExampleCommand endpoint'], request=ExampleCommandUpdateStatusSerializer
)
class ExampleCommandUpdateStatusAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ExampleCommandUpdateStatusSerializer(data=request.data)

        if serializer.is_valid():
            key_s3 = serializer.data.get('key_s3')
            err_body = serializer.data.get('err_body', None)

            if err_body:
                new_status = UserExampleCommand.StatusChoice.failure
            else:
                new_status = UserExampleCommand.StatusChoice.executed

            users_example_commands = UserExampleCommand.objects.filter(
                example_command__key_s3=key_s3)
            users_example_commands.update(status=new_status)
            invalidate_model(UserExampleCommand)

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
