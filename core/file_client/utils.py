import os

from django.conf import settings


def handle_file_upload(file, filename: str):
    path = os.path.join(settings.PATH_TO_LOCAL_STORAGE, filename)
    with open(path, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)

    return path