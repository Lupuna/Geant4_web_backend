from file_client.base_file_client import BaseRendererUploader


class ExampleRendererClient(BaseRendererUploader):

    def __init__(self, name: str, path: str = None, file_format='csv'):
        super().__init__(name, path, file_format)

        if not self.is_read_only:
            raise NotImplementedError('For Example only read_only_mode')

    def render(self):
        raise NotImplementedError('Method not allowed')


