from celery import shared_task

from . import download, send, remove


@shared_task
def download_file(file_data):
    download(file_data)


@shared_task
def upload_file(file_data):
    send(file_data)


@shared_task
def update_file(file_data):
    send(file_data, update=True)


@shared_task
def remove_file(file_data):
    remove(file_data)
