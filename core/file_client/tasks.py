from celery import shared_task

from file_client.example_csv_client import ExampleRendererClient
from file_client.profile_image_client import ProfileImageRendererClient


@shared_task
def render_and_upload_profile_image_task(old_file_path: str, new_name: str):
    client = ProfileImageRendererClient(name=new_name, path=old_file_path)
    return client.upload()


@shared_task
def render_and_update_profile_image_task(old_file_path: str, new_name: str):
    client = ProfileImageRendererClient(name=new_name, path=old_file_path)
    return client.update()


@shared_task
def render_and_upload_documentation_image_task(old_file_path: str, new_name: str):
    client = ProfileImageRendererClient(name=new_name, path=old_file_path)
    return client.upload()


@shared_task
def render_and_update_documentation_image_task(old_file_path: str, new_name: str):
    client = ProfileImageRendererClient(name=new_name, path=old_file_path)
    return client.update()


@shared_task
def destroy_documentation_image_task(name: str):
    client = ProfileImageRendererClient(name=name)
    return client.delete()


@shared_task
def destroy_documentation_graphic_task(name: str):
    client = ExampleRendererClient(name=name)
    return client.delete()
