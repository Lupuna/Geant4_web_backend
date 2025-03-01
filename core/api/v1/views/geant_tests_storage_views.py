from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import UpdateModelMixin

from api.v1.serializers.geant_tests_storage_serializers import VersionSerializer, TestResultSerializer, ModeSerializer

from geant_tests_storage.models import Version, TestResult, FileModeModel
from core.permissions import IsEmployeePermission, IsStaffPermission, InLimitedEmployeeGroupPermission

from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=['Change file mode']
)
class FileModeAPIView(UpdateModelMixin, GenericViewSet):
    permission_classes = (IsAuthenticated, IsStaffPermission, )
    serializer_class = ModeSerializer

    def get_object(self):
        return FileModeModel.objects.first()


@extend_schema(
    tags=['VersionViewSet']
)
class VersionAPIViewSet(ModelViewSet):
    serializer_class = VersionSerializer
    queryset = Version.objects.all()
    base_fail_perm_msg = 'Only {} can interact with versions'

    def get_file_mode(self):
        return FileModeModel.objects.first().mode

    def get_permissions(self):
        mode = self.get_file_mode()
        if mode == 3:
            return (IsAuthenticated(), IsEmployeePermission(), )
        elif mode == 2:
            return (IsAuthenticated(), InLimitedEmployeeGroupPermission(), )
        elif mode == 1:
            return (IsAuthenticated(), IsStaffPermission(), )
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

        return super().permission_denied(request, message, code)


@extend_schema(
    tags=['TestResultViewSet']
)
class TestResultAPIViewSet(ModelViewSet):
    serializer_class = TestResultSerializer
    base_fail_perm_msg = 'Only {} can interact with test results'

    def get_file_mode(self):
        return FileModeModel.objects.first().mode

    def get_queryset(self):
        version = self.kwargs.get('version_pk')
        queryset = TestResult.objects.filter(version=version)

        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            queryset = queryset.prefetch_related('files')
        return queryset

    def get_permissions(self):
        return VersionAPIViewSet.get_permissions(self)

    def permission_denied(self, request, message=None, code=None):
        message = self.base_fail_perm_msg
        mode = self.get_file_mode()

        if mode == 3:
            message = message.format('employees')
        elif mode == 2:
            message = message.format('part of employees')
        elif mode == 1:
            message = message.format('staff')

        return super().permission_denied(request, message, code)
