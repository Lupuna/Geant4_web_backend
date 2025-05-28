import shutil

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


class DocumentationImageRenderClient(BaseRendererUploader):

    def __init__(self, name: str, path: str = None, file_format='webp'):
        super().__init__(name, path, file_format)

    def render(self):
        super().render()

        with Image.open(self.path) as img:
            img.save(
                self.new_path,
                "WEBP",
                quality=50,
                method=6,
                optimize=True
            )


class ReadOnlyClient(BaseRendererUploader):

    def __init__(self, name: str, path: str = None, file_format='zip'):
        super().__init__(name, path, file_format)

        if not self.is_read_only:
            raise NotImplementedError('For Example only read_only_mode')

    def render(self):
        raise NotImplementedError('Method not allowed')


class DocumentationGraphicClient(BaseRendererUploader):
    def __init__(self, name: str, path: str = None, file_format='csv'):
        super().__init__(name, path, file_format)

    def render(self):
        super().render()

        shutil.copyfile(self.path, self.new_path)
