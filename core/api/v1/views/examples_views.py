import requests

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status

from .mixins import ElasticMixin

from api.v1.serializers.examples_serializers import (
    ExamplePOSTSerializer,
    ExampleGETSerializer,
    TagSerializer,
    ExamplePATCHSerializer,
    ExampleCommandGETSerializer,
    ExampleCommandPOSTSerializer,
    ExampleCommandUpdateStatusSerializer,
    DetailExampleSerializer
)
from api.tasks import send_celery_mail

from file_client.example_csv_client import ExampleRendererClient
from file_client.exceptions import FileClientException

from geant_examples.models import Example, Tag, UserExampleCommand, ExampleCommand
from geant_examples.documents import ExampleDocument

from drf_spectacular.utils import extend_schema

from django.conf import settings
from django.http import FileResponse
from django.db.models.query import QuerySet

from cacheops import invalidate_model


@extend_schema(
    tags=['Example ViewSet']
)
class ExampleViewSet(ModelViewSet, ElasticMixin):
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    elastic_document = ExampleDocument

    def get_serializer(self, *args, **kwargs):
        match self.request.method:
            case 'GET':
                if self.detail:
                    return DetailExampleSerializer(*args, **kwargs)
                return ExampleGETSerializer(*args, **kwargs)
            case 'POST':
                return ExamplePOSTSerializer(*args, **kwargs)
            case 'PATCH':
                return ExamplePATCHSerializer(*args, **kwargs)

    def get_queryset(self):
        elastic_document_class = self.get_elastic_document_class()
        search = elastic_document_class.search()
        result_search = self.elastic_full_query_handling(self.request, search)

        return result_search.to_queryset()


@extend_schema(
    tags=['ExampleCommand endpoint']
)
class ExampleCommandViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
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

    def get_queryset(self, *prefetch_lookups) -> QuerySet:
        example = int(self.kwargs.get('example_pk'))

        return ExampleCommand.objects.filter(example=example).prefetch_related(*prefetch_lookups)

    @extend_schema(request=ExampleCommandPOSTSerializer)
    def create(self, request, *args, **kwargs):
        params = request.data.get('params', {})
        user = request.user
        example = Example.objects.get(id=self.kwargs.get('example_pk'))
        key_s3 = self._generate_key_s3(example.title_not_verbose, params)
        request.data['params'] = key_s3
        filename = key_s3 + '.zip'

        client = ExampleRendererClient(filename)
        try:
            response = client.download()
        except FileClientException as e:
            ex_commands = self.get_queryset(
                'example', 'users').filter(key_s3=key_s3)
            if not ex_commands.exists():
                response = self._run_example(request, example, params)
            else:
                response = self._example_executed(ex_commands, user)

            return response

        self._add_user_in_example_command(example, key_s3, user)
        return FileResponse(response, as_attachment=True, filename=filename)

    @staticmethod
    def _generate_key_s3(title, params):
        str_params = {
            str(k).replace(' ', '---'): str(v).replace(' ', '---')
            for k, v in params.items()
        }
        return f'key-s3-{title}___' + '___'.join(f'{k}={v}' for k, v in str_params.items())

    def _run_example(self, request, example, params):
        data = {
            'title': example.title_not_verbose,
            'commands': [{k: str(v)} for k, v in params.items()]
        }
        response = requests.post(
            settings.GEANT_BACKEND_RUN_EXAMPLE_URL, json=data)
        if response.status_code == 200:
            return super().create(request)

        return Response(
            data=response.json(),
            status=response.status_code,
            headers=response.headers
        )

    def _example_executed(self, ex_commands, user):
        ex_command = ex_commands.first()
        if user not in ex_command.users.all():
            ex_command.users.add(user)
        return Response(
            {'detail': 'Example already executed, wait for results'},
            status=status.HTTP_200_OK
        )

    @staticmethod
    def _add_user_in_example_command(example, key_s3, user):
        ex_command, created = ExampleCommand.objects.get_or_create(
            key_s3=key_s3, example=example)

        if user not in ex_command.users.all():
            ex_command.users.add(user)

        us_ex_command = ex_command.users.through.objects.get(user=user)
        us_ex_command.status = UserExampleCommand.StatusChoice.executed
        us_ex_command.save()


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
                example_command__key_s3=key_s3).prefetch_related('user', 'example_command')
            ex_command = users_example_commands.first().example_command
            user_emails = ex_command.users.values_list('email', flat=True)
            old_status = users_example_commands.first().get_status_display()
            title_verbose = users_example_commands.first().example_command.example.title_verbose
            users_example_commands.update(status=new_status)
            invalidate_model(UserExampleCommand)
            message = f'The simulation of the example "{title_verbose}" with the key {key_s3} changed the status from "{old_status}" to "{new_status.label}"'
            topic = 'Simulation status'
            send_celery_mail.delay(
                topic,
                message,
                list(user_emails)
            )

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Categories']
)
class CategoryAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        data = {label: val for label, val in Example.CategoryChoices.choices}

        return Response(data, status=status.HTTP_200_OK)
