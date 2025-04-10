import os

from abc import ABC, abstractmethod
from django.conf import settings
from loguru import logger

from file_client.S3_client import S3FileLoader


def render_then_cleanup(method):
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
    def __init__(self, path: str, new_name: str):
        self.path = path
        self.new_filename = f"{os.path.splitext(new_name)[0]}.{self.format}"
        self.new_path = os.path.join(settings.PATH_TO_LOCAL_STORAGE, self.new_filename)
        self.loader = S3FileLoader(path=self.new_path)

    @property
    def format(self):
        return 'webp'

    @render_then_cleanup
    def upload(self):
        return self.loader.upload()

    @render_then_cleanup
    def update(self):
        return self.loader.update()

    def cleanup(self):
        if os.path.exists(self.new_path):
            os.remove(self.new_path)

        if os.path.exists(self.path):
            os.remove(self.path)

    @abstractmethod
    def render(self):
        ...
