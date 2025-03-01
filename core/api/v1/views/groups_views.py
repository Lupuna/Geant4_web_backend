from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status

from api.v1.serializers.groups_serializers import LimitedEmployeeGroupDELETESerializer, LimitedEmployeeGroupPATCHSerializer

from users.auth.utils import response_cookies

from drf_spectacular.utils import extend_schema

from core.permissions import IsStaffPermission

from django.contrib.auth.models import Group


@extend_schema(
    tags=['Manage LimitedEmployeeGroup'],
    request=LimitedEmployeeGroupDELETESerializer
)
class LimitedEmployeeGroupAPIViewSet(GenericViewSet):
    permission_classes = (IsAuthenticated, IsStaffPermission, )

    def get_object(self):
        return Group.objects.get(name='LimitedEmployeeGroup')

    @action(methods=['post', ], detail=False, url_path='rm_users', url_name='rm-users')
    def delete_users(self, request):
        serializer = LimitedEmployeeGroupDELETESerializer(
            instance=self.get_object(), data=request.data)

        if serializer.is_valid():
            deleted_usernames = serializer.delete(
                instance=self.get_object(), validated_data=serializer.validated_data)
            data = {
                'detail': f'Theese users: ({', '.join(deleted_usernames)}) - was remove from LimitedEmployeeGroup'}

            return response_cookies(data, status=status.HTTP_200_OK)

        return response_cookies(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', ], detail=False, url_path='add_users', url_name='add-users')
    def add_users(self, request, *args, **kwargs):
        serializer = LimitedEmployeeGroupPATCHSerializer(
            instance=self.get_object(), data=request.data)

        if serializer.is_valid():
            usernames_added = serializer.save()
            data = {
                'detail': f'Theese users: ({', '.join(usernames_added)}) - added into LimitedEmployeeGroup'}

            return response_cookies(data, status=status.HTTP_200_OK)

        return response_cookies(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
