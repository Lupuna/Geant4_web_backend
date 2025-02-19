from django.urls import path
from api.v1.views.files_views import DownloadTemporaryFileAPIWiew, UploadTemporaryFileAPIView, UpdateTemporaryFileAPIView, RemoveTemporaryFileAPIView


urlpatterns = [
    path('download/', DownloadTemporaryFileAPIWiew.as_view(),
         name='download-file'),
    path('upload/', UploadTemporaryFileAPIView.as_view(), name='upload-file'),
    path('update/', UpdateTemporaryFileAPIView.as_view(), name='update-file'),
    path('remove/', RemoveTemporaryFileAPIView.as_view(), name='remove-file')
]
