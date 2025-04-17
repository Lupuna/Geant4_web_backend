from PIL import Image

from file_client.base_file_client import BaseRendererUploader


class ProfileImageRendererClient(BaseRendererUploader):

    def __init__(self, name: str, path: str = None, file_format='webp'):
        super().__init__(name, path, file_format)

    def render(self):
        super().render()

        with Image.open(self.path) as img:
            img.save(
                self.new_path,
                self.format,
                optimize=True,
                quality=10
            )
