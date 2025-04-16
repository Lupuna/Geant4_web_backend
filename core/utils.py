import requests

from django.conf import settings
from loguru import logger

class DatabaseSynchronizer:
    def __init__(self, example=None, command=None):
        self.example = example or command.example
        self.commands = list(self.example.commands.all())

    def prepare_data(self):
        commands = self.prepare_commands()
        return {
            "title": self.example.title_not_verbose,
            "commands": commands
        }

    def prepare_commands(self):
        return [
            {
                "title": command.title,
                "order_index": command.order_index,
                "default": command.default
            }
            for command in self.commands
        ]

    def get_example_from_backend(self):
        try:
            response = requests.get(
                url=settings.GEANT_BACKEND_GET_EXAMPLE_URL.format(title=self.example.title_not_verbose)
            )
        except Exception as e:
            logger.error(e)
            raise e
        else:
            data = response.json()
            if data.get("detail") == "Example not found":
                return -1
            return data["id"]

    def drop_example(self, backend_example_id=None):
        backend_example_id = backend_example_id or self.get_example_from_backend()
        if backend_example_id == -1:
            logger.info("example %s not found on Backend service." % self.example.title_not_verbose)
            return

        url = settings.GEANT_BACKEND_DELETE_EXAMPLE_URL.format(id=backend_example_id)
        try:
            requests.delete(url)
        except Exception as e:
            logger.error(e)
        else:
            logger.info("success delete %s example from Backend." % self.example.title_not_verbose)

    def create_example(self):
        json = self.prepare_data()
        try:
            response = requests.post(
                url=settings.GEANT_BACKEND_CREATE_EXAMPLE_URL,
                json=json
            )
        except Exception as e:
            logger.error(e)
            raise e
        else:
            logger.info("success create example %s on Backend service." % self.example.title_not_verbose)

    def run(self):
        backend_example_id = self.get_example_from_backend()
        if backend_example_id != -1:
            self.drop_example(backend_example_id)

        self.create_example()

        logger.info(f"success sync example ({self.example.title_not_verbose}) with backend service")