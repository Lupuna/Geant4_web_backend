from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status

from api.v1.serializers.groups_serializers import GroupPATCHSerializer, GroupPOSTSerializer

from users.auth.utils import response_cookies

from drf_spectacular.utils import extend_schema

from core.permissions import IsStaffPermission

from django.contrib.auth.models import Group


@extend_schema(
    tags=['Group ViewSet'],
)
class GroupAPIViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, IsStaffPermission, )
    queryset = Group.objects.all().prefetch_related('user_set', 'permissions')
    http_method_names = ('get', 'post', 'delete', 'patch', )

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'PATCH':
            return GroupPATCHSerializer(*args, **kwargs)
        else:
            return GroupPOSTSerializer(*args, **kwargs)

    @action(methods=['patch', ], detail=True, url_path='rm_objs', url_name='rm-objs')
    def delete_objs(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            instance=self.get_object(), data=request.data, context={'delete': True})

        if serializer.is_valid():
            delete_info = serializer.save()

            return response_cookies(delete_info, status=status.HTTP_200_OK)

        return response_cookies(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
