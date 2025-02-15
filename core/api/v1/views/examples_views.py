from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from api.v1.serializers.examples_serializers import ExamplePOSTSerializer, ExampleGETSerializer, TagSerializer, ExamplePATCHSerializer

from users.models import User

from geant_examples.models import Example, Tag, UserExample

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
            case _:
                raise ValueError(
                    'Cannot get serializer for current HTTP method')

    def create(self, request, *args, **kwargs):
        params = request.data.pop('params', {})

        if params:
            str_params_vals = {str(key): str(val)
                               for key, val in params.items()}
            key_s3 = 'key-s3_' + '_'.join('_'.join(key_val)
                                          for key_val in str_params_vals.items())
            request.data.setdefault('params', key_s3)

        response = super().create(request, *args, **kwargs)
        del response.data['params']
        response.data.setdefault('key_s3', key_s3)

        return response
