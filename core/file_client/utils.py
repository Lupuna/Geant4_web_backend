import os

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile


def handle_file_upload(file: UploadedFile) -> str:
    filename = file.name
    path = os.path.join(settings.PATH_TO_LOCAL_STORAGE, filename)
    with open(path, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)

    return path