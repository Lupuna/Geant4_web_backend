from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from api.v1.serializers.examples_serializers import (
    ExamplePOSTSerializer,
    ExampleGETSerializer,
    TagSerializer,
    ExamplePATCHSerializer,
    ExampleGeantGETSerializer,
    ExampleGeantPOSTSerializer
)

from users.models import User

from geant_examples.models import Example, Tag, UserExample, ExampleGeant, ExamplesTitleRelation

from drf_spectacular.utils import extend_schema

from rest_framework.permissions import IsAuthenticated


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
    tags=['ExampleGeant endpoint']
)
class ExampleGeantViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, )
    http_method_names = ['get', 'post', 'delete', ]

    def get_serializer(self, *args, **kwargs):
        if self.request.method in ['GET', ]:
            return ExampleGeantGETSerializer(*args, **kwargs)

        if self.request.method in ['POST', ]:
            kwargs.setdefault('context', self.get_serializer_context())
            return ExampleGeantPOSTSerializer(*args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.setdefault('example_pk', int(self.kwargs['example_pk']))

        return context

    def get_queryset(self):
        example = int(self.kwargs.get('example_pk'))

        return ExampleGeant.objects.filter(example=example)

    @extend_schema(request=ExampleGeantPOSTSerializer)
    def create(self, request, *args, **kwargs):
        params = request.data.get('params', {})

        if params:
            str_params_vals = {str(key): str(val)
                               for key, val in params.items()}
            key_s3 = 'key-s3_' + '_'.join('_'.join(key_val)
                                          for key_val in str_params_vals.items())
            request.data['params'] = key_s3

        response = super().create(request, *args, **kwargs)
        info_serializer = ExampleGeantGETSerializer(
            instance=ExampleGeant.objects.get(key_s3=key_s3))
        response.data = info_serializer.data

        return response
