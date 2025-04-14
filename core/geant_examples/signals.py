import requests

from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
from loguru import logger

from .models import Example, Command

def send_request(instance, delete=False):
    example, commands = [None] * 2

    if isinstance(instance, Command):
        example = instance.example
        commands = [instance]

    if isinstance(instance, Example):
        example = instance
        commands = instance.commands

    if (example and commands) is not None:
        json = {
            "title": example.title_not_verbose,
            "commands": [{
                "title": command.title,
                "order_index": command.order_index,
                "default": command.default
            } for command in commands]
        }
        url = settings.BACKEND_GET_EXAMPLE_URL.format(title=example.title_not_verbose)
        response = requests.get(url=url)
        response_data = response.json()
        if response_data.get("detail") is None:
            json["to_delete"] = delete
            response = requests.patch(
                url=settings.BACKEND_DELETE_EXAMPLE_URL.format(id=response_data["id"]),
                json=json
            )
            if not response.ok:
                raise ValueError(f"Failed. {response.json()}")

            message = f"successful {'delete' if delete else 'update'} Example on Backend Service."
            logger.info(message)
        else:
            response = requests.post(
                url=settings.BACKEND_CREATE_EXAMPLE_URL,
                json=json
            )
            if not response.ok:
                raise ValueError(f"Failed. {response.json()}")

            logger.info("successful create Example on Backend Service.")

@receiver(pre_delete, sender=Command)
def delete_command_on_backend_service(sender, instance, **kwargs):
    example = instance.example
    backend_example = requests.get(
        url=settings.BACKEND_GET_EXAMPLE_URL.format(title=example.title_not_verbose)
    ).json()
    backend_example_id = backend_example["id"]

    json = {
        "title": example.title_not_verbose,
        "commands": [{
            "title": instance.title,
            "order_index": instance.order_index,
            "default": instance.default
        }],
        "to_delete": True
    }
    backend_command_response = requests.patch(
        url=settings.BACKEND_UPDATE_EXAMPLE_URL.format(id=backend_example_id),
        json=json
    )
    if not backend_command_response.ok:
        raise ValueError(backend_command_response.json())

    logger.info("success update command of example on Backend Service.")

@receiver(pre_delete, sender=Example)
def delete_example_on_backend_service(sender, instance, **kwargs):
    backend_example = requests.get(
        url=settings.BACKEND_GET_EXAMPLE_URL.format(title=instance.title_not_verbose)
    ).json()
    if backend_example:
        backend_example_id = backend_example["id"]
        backend_delete_response = requests.delete(
            url=settings.BACKEND_DELETE_EXAMPLE_URL.format(id=backend_example_id)
        )
        if not backend_delete_response.ok:
            raise ValueError(backend_delete_response.json())

        logger.info("success delete example on Backend Service.")

@receiver(pre_save, sender=Example)
def save_example_on_backend_service(sender, instance, **kwargs):
    backend_example = requests.get(
        url=settings.BACKEND_GET_EXAMPLE_URL.format(title=instance.title_not_verbose)
    ).json()

    if backend_example.get("detail") == "Example not found":
        backend_example_response = requests.post(
            url=settings.BACKEND_CREATE_EXAMPLE_URL,
            json={
                "title": instance.title_not_verbose,
                "commands": [{
                    "title": command.title,
                    "order_index": command.order_index,
                    "default": command.default
                } for command in Command.objects.filter(example__title_not_verbose=instance.title_not_verbose)]
            }
        )
        if not backend_example_response.ok:
            raise ValueError(backend_example_response.json())

        logger.info("success create example on Backend Service.")
    else:
        backend_example_id = backend_example["id"]
        json = {
            "title": instance.title_not_verbose,
            "commands": [{
                "title": command.title,
                "order_index": command.order_index,
                "default": command.default
            } for command in instance.commands.all()],
            "to_delete": False
        }
        backend_update_response = requests.patch(
            url=settings.BACKEND_UPDATE_EXAMPLE_URL.format(id=backend_example_id),
            json=json
        )
        if not backend_update_response.ok:
            raise ValueError(backend_update_response.json())

        logger.info("success update example on Backend Service.")

@receiver(pre_save, sender=Command)
def save_command_on_backend_service(sender, instance, **kwargs):
    example = instance.example
    backend_example = requests.get(
        url=settings.BACKEND_GET_EXAMPLE_URL.format(title=example.title_not_verbose)
    ).json()
    backend_example_id = backend_example["id"]

    json = {
        "title": example.title_not_verbose,
        "commands": [{
            "title": instance.title,
            "order_index": instance.order_index,
            "default": instance.default
        }],
        "to_delete": False
    }
    backend_command_response = requests.patch(
        url=settings.BACKEND_UPDATE_EXAMPLE_URL.format(id=backend_example_id),
        json=json
    )
    if not backend_command_response.ok:
        raise ValueError(backend_command_response.json())

    logger.info("success update command of example on Backend Service.")