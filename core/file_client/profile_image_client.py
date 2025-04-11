from PIL import Image

from file_client.base_file_client import BaseRendererUploader


class ProfileImageRendererClient(BaseRendererUploader):

    @property
    def format(self):
        return 'png'

    def render(self):
        with Image.open(self.path) as img:
            img.save(self.new_path, 'png')
