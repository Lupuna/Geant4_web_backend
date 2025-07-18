import ntpath
import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from io import BytesIO

import requests

from django.conf import settings


@dataclass
class Endpoint:
    upload = settings.STORAGE_URL + "/upload/"
    update = settings.STORAGE_URL + "/update/"
    retrieve = settings.STORAGE_URL + "/retrieve/"
    remove = settings.STORAGE_URL + "/remove/"


class S3FileLoader:
    def __init__(self, path: str | None):
        self.path = path
        self.format = "zip"
        self.filename = self.extract_name()

    def extract_name(self):
        head, tail = ntpath.split(self.path)
        if tail:
            return tail
        return ntpath.basename(head) + ".%s" % self.format

    def sender(self, url, stream=False, temporary=False, data=None, json=None, file=False):
        if stream:
            response = requests.post(url=url, data=data, json=json)
            path = os.path.join(settings.PATH_TO_LOCAL_STORAGE, self.filename)
            if response.ok:
                with open(path, "wb") as file:
                    file.write(response.content)
            else:
                return response.json()
        elif temporary:
            response = requests.post(url=url, data=data, json=json)
            if response.ok:
                return BytesIO(response.content)
            else:
                return response.json()
        elif file:
            with self.file_after_process() as _file:
                files = {'file': _file}
                response = requests.post(url=url, json=json, files=files)
                return response.json()
        else:
            response = requests.post(url=url, json=json, data=data)
            return response.json()

    @contextmanager
    def file_after_process(self):
        self.format = "zip"
        if os.path.isdir(self.path):
            head, tail = ntpath.split(self.path)
            directory = ntpath.basename(head)
            with tempfile.TemporaryDirectory() as tmp_directory:
                base_name = os.path.join(tmp_directory, directory)
                shutil.make_archive(base_name=base_name,
                                    format=self.format, root_dir=self.path)
                filepath = base_name + ".%s" % self.format
                with open(filepath, 'rb') as file:
                    yield file
        else:
            with open(self.path, 'rb') as file:
                yield file

    def upload(self):
        return self.sender(url=Endpoint.upload, file=True)

    def update(self):
        return self.sender(url=Endpoint.update, file=True)

    def download_stream(self, filename):
        return self.sender(url=Endpoint.retrieve, stream=True, json={'filename': filename})

    def download_temporary(self, filename):
        return self.sender(url=Endpoint.retrieve, temporary=True, json={'filename': filename})

    def delete(self, filename):
        return self.sender(url=Endpoint.remove, json={'filename': filename})
