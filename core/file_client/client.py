import os

from django.conf import settings

from file_client.tasks import download_file, upload_file, update_file, remove_file


PATH_TO_LOCAL_STORAGE = settings.PATH_TO_LOCAL_STORAGE


class FileLoader:
    def __init__(self, file_data: dict):
        self.file_data = file_data

    @property
    def filename(self):
        return self.file_data['filename']

    @property
    def local_dir(self):
        return PATH_TO_LOCAL_STORAGE + self.filename

    @property
    def file_format(self):
        return self.filename.split('.')[-1]

    @property
    def exists(self):
        return os.path.exists(self.local_dir)

    def download(self):
        if not self.exists:
            download_file.delay(self.file_data)
        else:
            raise ValueError('File with the same name already exists')

    def upload(self):
        if self.exists:
            upload_file.delay(self.filename)

    def update(self):
        if self.exists:
            update_file.delay(self.filename)

    def remove(self):
        remove_file.delay(self.file_data)

        if self.exists:
            os.remove(self.local_dir)
