from rest_framework.viewsets import ModelViewSet
from api.v1.serializers.geant_tests_storage_serializers import VersionSerializer, TestResultSerializer
from geant_tests_storage.models import Version, TestResult


class VersionAPIViewSet(ModelViewSet):
    serializer_class = VersionSerializer
    queryset = Version.objects.all()


class TestResultAPIViewSet(ModelViewSet):
    serializer_class = TestResultSerializer

    def get_queryset(self):
        version = self.kwargs.get('version_pk')
        queryset = TestResult.objects.filter(version=version)

        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            queryset = queryset.prefetch_related('files')
        return queryset

