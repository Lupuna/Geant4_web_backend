from math import ceil

import loguru
import requests
from cacheops import invalidate_model
from django.conf import settings
from django.db.models.query import QuerySet, Prefetch
from django.http import FileResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.tasks import send_celery_mail_advanced
from api.v1.serializers.examples_serializers import (
    ExamplePOSTSerializer,
    ExampleGETSerializer,
    ExamplePATCHSerializer,
    ExampleCommandGETSerializer,
    ExampleCommandPOSTSerializer,
    ExampleCommandUpdateStatusSerializer,
    DetailExampleSerializer, CategorySerializer
)
from file_client.exceptions import FileClientException
from file_client.files_clients import ReadOnlyClient
from geant_examples.documents import ExampleDocument
from geant_examples.models import Example, UserExampleCommand, ExampleCommand, Command, CommandValue, Category
from .mixins import ElasticMixin


@extend_schema(
    tags=['Example Categories']
)
class CategoryViewSet(ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


@extend_schema(
    tags=['Example ViewSet']
)
class ExampleViewSet(ModelViewSet, ElasticMixin):
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    elastic_document = ExampleDocument

    @extend_schema(exclude=True)
    @action(detail=False, methods=['patch'], url_path="change-synchronized", permission_classes=[])
    def change_synchronized_status(self, request, pk=None):
        title_not_verbose = request.query_params.get("title_not_verbose", None)
        try:
            example = Example.objects.get(title_not_verbose=title_not_verbose)
            example.synchronized = False
            example.save()
        except Exception as e:
            return Response({"message": f"error. {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "success."}, status=status.HTTP_200_OK)

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
        if self.action == 'list':
            elastic_document_class = self.get_elastic_document_class()
            self.setup_elastic_document_conf()
            search = elastic_document_class.search()
            result_search = self.elastic_full_query_handling(self.request, search)
            return result_search.to_queryset()
        return Example.objects.prefetch_related(
            'tags',
            Prefetch(
                'commands',
                queryset=Command.objects.prefetch_related(
                    'command_list',
                    Prefetch(
                        'command_list__command_values',
                        queryset=CommandValue.objects.only('value'),
                        to_attr='prefetched_command_values'
                    )
                )
            )
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data.append(
            {"pages_count": ceil(len(response.data) / self.elastic_document_conf["pagination_page_size"])})
        return response


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
        example = get_object_or_404(Example, id=self.kwargs.get('example_pk'))
        for command in example.commands.all():
            if command.title in params.keys():
                params[command.title] = [params[command.title], command.order_index]

        key_s3 = self._generate_key_s3(example.title_not_verbose, params)
        request.data['params'] = key_s3
        filename = key_s3 + '.zip'

        client = ReadOnlyClient(filename)
        try:
            response = client.download()
        except FileClientException as e:
            ex_commands = self.get_queryset(
                'example', 'users').filter(key_s3=key_s3)
            if not ex_commands.exists():
                response = self._run_example(request, example, params)
            else:
                ex_command = ex_commands.first()
                us_ex_commands = UserExampleCommand.objects.filter(
                    example_command=ex_command)
                status_val = us_ex_commands.values_list(
                    'status', flat=True).first()
                if status_val == 2:
                    ex_command.users.add(user)
                    us_ex_commands.update(
                        status=UserExampleCommand.StatusChoice.failure)
                    invalidate_model(UserExampleCommand)
                    return Response({'detail': 'Example executing was finished in error'},
                                    status=status.HTTP_400_BAD_REQUEST)
                response = self._example_is_executing(ex_commands, user)
            return response

        self._add_user_in_example_command(example, key_s3, user)
        return FileResponse(response, as_attachment=True, filename=filename)

    @staticmethod
    def _generate_key_s3(title, params):
        str_params = {
            str(v[-1]): str(v[0]).replace(' ', '--')
            for k, v in params.items()
        }
        return f'key-s3-{title}__' + '__'.join(f'{k}={v}' for k, v in str_params.items())

    def _run_example(self, request, example, params):
        data = {
            'title': example.title_not_verbose,
            'commands': [{k: str(v[0])} for k, v in params.items()]
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

    def _example_is_executing(self, ex_commands, user):
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

        us_ex_command = ex_command.users.through.objects.get(
            user=user, example_command=ex_command)
        us_ex_command.status = UserExampleCommand.StatusChoice.executed
        us_ex_command.save()


@extend_schema(
    tags=['ExampleCommand endpoint'], request=ExampleCommandUpdateStatusSerializer
)
class ExampleCommandUpdateStatusAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ExampleCommandUpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        key_s3 = serializer.validated_data['key_s3']
        err_body = serializer.validated_data.get('err_body')
        new_status = (
            UserExampleCommand.StatusChoice.failure
            if err_body
            else UserExampleCommand.StatusChoice.executed
        )
        users_example_commands = UserExampleCommand.objects.select_related(
            'example_command__example'
        ).filter(
            example_command__key_s3=key_s3
        )

        if not users_example_commands.exists():
            return Response({"detail": "Команды не найдены"}, status=status.HTTP_404_NOT_FOUND)

        first_command = users_example_commands[0]
        example_command = first_command.example_command
        example_id = example_command.id
        title_verbose = example_command.example.title_verbose
        old_status_label = first_command.status
        user_emails = list(example_command.users.values_list('email', flat=True))
        users_example_commands.update(status=new_status)
        invalidate_model(UserExampleCommand)
        topic = 'Статус симуляции'
        message = (
            f'Статус симуляции примера "{title_verbose}" с ключом {key_s3} '
            f'изменён с "{old_status_label}" на "{new_status.label}"'
        )

        send_celery_mail_advanced.delay(
            subject=topic,
            message=message,
            recipients=user_emails,
            html_template='emails/result.html',
            context={
                'title': title_verbose,
                'status': new_status.label,
                'result_link': f"{settings.FRONTEND_URL}/profile/"
            }
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
