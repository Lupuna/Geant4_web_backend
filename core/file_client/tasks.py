from celery import shared_task
from file_client.profile_image_client import ProfileImageRendererClient


@shared_task
def render_and_upload_task(old_file_path: str, new_name: str):
    client = ProfileImageRendererClient(path=old_file_path, new_name=new_name)
    return client.upload()


@shared_task
def render_and_update_task(old_file_path: str, new_name: str):
    client = ProfileImageRendererClient(path=old_file_path, new_name=new_name)
    return client.update()
