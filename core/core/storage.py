import requests
import os

from tempfile import TemporaryDirectory
from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import Storage

class BackupStorage(Storage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = "web-backend-backup.bin"
        self.init_backup()

    def init_backup(self):
        response = requests.post(
            url=settings.STORAGE_URL + "/upload/",
            files={"file": (self.filename, b"")}
        )
        response.raise_for_status()

    def _open(self, name, mode="rb"):
        response = requests.post(
            url=settings.STORAGE_URL + "/retrieve/",
            json={
                "filename": self.filename
            }
        )
        response.raise_for_status()
        with TemporaryDirectory() as directory:
            path = os.path.join(directory, self.filename)
            with open(path, 'wb') as f:
                f.write(response.content)

            return File(
                open(path, mode),
                name=self.filename
            )

    def _save(self, name, content):
        response = requests.post(
            url=settings.STORAGE_URL + "/update/",
            files={"file": (self.filename, content.open(mode="rb"))}
        )
        response.raise_for_status()
        return name

    def exists(self, name):
        ...
