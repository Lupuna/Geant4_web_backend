from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import UpdateModelMixin
from rest_framework.exceptions import PermissionDenied, NotAuthenticated

from api.v1.serializers.geant_tests_storage_serializers import VersionSerializer, TestResultSerializer, ModeSerializer

from geant_tests_storage.models import Version, TestResult, FileModeModel
from core.permissions import IsStaffPermission, GroupPermission

from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=['Change file mode']
)
class FileModeAPIView(UpdateModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated, IsStaffPermission, )
    serializer_class = ModeSerializer

    def get_object(self):
        return FileModeModel.objects.first()


class BaseTestStorageViewSet(ModelViewSet):
    model_name = None
    base_fail_perm_msg = 'Only {} ' + \
        f'can interact with {model_name} or group(s) you are in has no permission for this action'

    def get_file_mode(self):
        return FileModeModel.objects.first().mode

    def get_permissions(self):
        mode = self.get_file_mode()

        if mode == 1:
            return IsAuthenticated(), IsStaffPermission()
        if mode == 2:
            return IsAuthenticated(), GroupPermission(self.model_name, self.request.method)
        if mode == 3:
            return IsAuthenticated(), GroupPermission(self.model_name, self.request.method, 'Employees')
        else:
            raise ValueError('Error occured: file mode did not define')

    def permission_denied(self, request, message=None, code=None):
        mode = self.get_file_mode()
        message = self.base_fail_perm_msg

        if mode == 3:
            message = message.format('employees')
        elif mode == 2:
            message = message.format('part of employees')
        elif mode == 1:
            message = message.format('staff')

        if request.authenticators and not request.successful_authenticator:
            raise NotAuthenticated()
        raise PermissionDenied(detail=message, code=code)


@extend_schema(
    tags=['VersionViewSet']
)
class VersionAPIViewSet(BaseTestStorageViewSet):
    serializer_class = VersionSerializer
    queryset = Version.objects.all()
    model_name = 'Version'
    base_fail_perm_msg = 'Only {} ' + \
        f'can interact with {model_name} or group(s) you are in has no permission for this action'


@extend_schema(
    tags=['TestResultViewSet']
)
class TestResultAPIViewSet(BaseTestStorageViewSet):
    serializer_class = TestResultSerializer
    model_name = 'TestResult'
    base_fail_perm_msg = 'Only {} ' + \
        f'can interact with {model_name} or group(s) you are in has no permission for this action'

    def get_queryset(self):
        version = self.kwargs.get('version_pk')
        queryset = TestResult.objects.filter(version=version)

        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            queryset = queryset.prefetch_related('files')
        return queryset
