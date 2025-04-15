import os

from abc import ABC, abstractmethod
from functools import wraps
from io import BytesIO

from django.conf import settings
from loguru import logger

from file_client.S3_client import S3FileLoader
from file_client.exceptions import FileClientException


def render_then_cleanup(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            self.render()
            return method(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error during file processing: {e}")
            raise
        finally:
            self.cleanup()

    return wrapper


class BaseRendererUploader(ABC):
    def __init__(self, name: str, path: str = None, file_format='webp'):
        self.is_read_only = not path
        self.format = file_format

        self.filename = f"{os.path.splitext(name)[0]}.{self.format}"

        self.path = path if not self.is_read_only else os.path.join(settings.PATH_TO_LOCAL_STORAGE, self.filename)
        self.new_path = self.path if self.is_read_only else os.path.join(settings.PATH_TO_LOCAL_STORAGE, self.filename)

        self.loader = S3FileLoader(path=self.new_path)

    def download_stream(self):
        self.check_is_read_only()

        response = self.loader.download_stream(self.filename)
        if response:
            raise FileClientException(404, {"detail": "Downloaded file not found on disk."})

        return self.path

    def download(self) -> BytesIO:
        self.check_is_read_only()

        response = self.loader.download_temporary(self.filename)
        if isinstance(response, BytesIO):
            return response
        raise FileClientException(404, {"detail": "Downloaded file not found S3"})

    def delete(self):
        self.check_is_read_only()
        return self.loader.delete(self.filename)

    def check_is_read_only(self):
        if not self.is_read_only:
            raise RuntimeError("Method not supported without read-only mode")

    @render_then_cleanup
    def upload(self):
        self.check_is_not_read_only()
        return self.loader.upload()

    @render_then_cleanup
    def update(self):
        self.check_is_not_read_only()
        return self.loader.update()

    def check_is_not_read_only(self):
        if self.is_read_only:
            raise RuntimeError("Method not supported in read-only mode")

    def cleanup(self):
        if os.path.exists(self.new_path):
            os.remove(self.new_path)

        if os.path.exists(self.path):
            os.remove(self.path)

    @abstractmethod
    def render(self):
        if self.is_read_only:
            raise NotImplementedError("Render not needed in read-only mode")
