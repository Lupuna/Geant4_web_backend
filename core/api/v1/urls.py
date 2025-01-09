from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

from api.v1.views.geant_tests_storage_views import VersionAPIViewSet, TestResultAPIViewSet

version_router = SimpleRouter()
version_router.register(r'versions', VersionAPIViewSet, basename='version')

test_result_router = NestedSimpleRouter(version_router, r'versions', lookup='version')
test_result_router.register(r'tests-results', TestResultAPIViewSet, basename='version-test-result')


urlpatterns = [
    path('', include(version_router.urls)),
    path('', include(test_result_router.urls))
]
