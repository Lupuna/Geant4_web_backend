from django.urls import path, include

from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

from api.v1.views.geant_tests_storage_views import VersionAPIViewSet, TestResultAPIViewSet
from api.v1.views.users_views import UserProfileViewSet, UserProfileUpdateImportantInfoViewSet
from api.v1.views.auth_views import RegistrationAPIView, LoginAPIView, GetAccessTokenView, LogoutAPIView
from api.v1.views.examples_views import ExampleViewSet, ExampleGeantViewSet
from api.v1.views.files_views import (
    DownloadTemporaryFileAPIWiew,
    UploadTemporaryFileAPIView,
    UpdateTemporaryFileAPIView,
    RemoveTemporaryFileAPIView
)


version_router = SimpleRouter()
version_router.register(r'versions', VersionAPIViewSet, basename='version')

test_result_router = NestedSimpleRouter(
    version_router, r'versions', lookup='version')
test_result_router.register(
    r'tests-results', TestResultAPIViewSet, basename='version-test-result')

user_update_router = SimpleRouter()
user_update_router.register(
    r'profile', UserProfileUpdateImportantInfoViewSet, basename='user-profile')

example_router = SimpleRouter()
example_router.register(r'examples', ExampleViewSet, basename='examples')

example_geant_router = NestedSimpleRouter(
    parent_router=example_router, parent_prefix=r'examples', lookup='example')
example_geant_router.register(
    r'example_geant', ExampleGeantViewSet, basename='example-example-geant')

urlpatterns = [
    path('', include(version_router.urls)),
    path('', include(test_result_router.urls)),
    path('', include(example_router.urls)),
    path('', include(user_update_router.urls)),
    path('', include(example_geant_router.urls)),
    path('registration/', RegistrationAPIView.as_view(), name='registration'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('token/refresh/', GetAccessTokenView.as_view(), name='refresh'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('profile/', UserProfileViewSet.as_view(
        actions=UserProfileViewSet.get_actions()), name='user-profile'),
    path('files/download/', DownloadTemporaryFileAPIWiew.as_view(),
         name='download-file'),
    path('files/upload/', UploadTemporaryFileAPIView.as_view(), name='upload-file'),
    path('files/update/', UpdateTemporaryFileAPIView.as_view(), name='update-file'),
    path('files/remove/', RemoveTemporaryFileAPIView.as_view(), name='remove-file'),
]
