import requests
import os

from celery import shared_task

from django.conf import settings

from dataclasses import dataclass


PATH_TO_LOCAL_STORAGE = settings.PATH_TO_LOCAL_STORAGE
STORAGE_URL = settings.STORAGE_URL


@dataclass
class Endpoint:
    upload = STORAGE_URL + "upload/"
    update = STORAGE_URL + "update/"
    download = STORAGE_URL + "retrieve/"
    remove = STORAGE_URL + "remove/"


@shared_task
def download_file(file_data):
    def download(file_data):
        download_url = Endpoint.download
        response = requests.post(url=download_url, json=file_data)
        response.raise_for_status()
        content_disposition = response.headers.get('Content-Disposition', None)

        if not content_disposition:
            raise ValueError('Cannot extract Content-Desposition from headers')

        out_file_name = content_disposition.split('filename=')[-1].strip('"')
        local_file_dir = PATH_TO_LOCAL_STORAGE + out_file_name

        with open(local_file_dir, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    download(file_data)


@shared_task
def upload_file(filename):
    def upload(filename):
        upload_url = Endpoint.upload
        local_file_dir = PATH_TO_LOCAL_STORAGE + filename

        with open(local_file_dir, 'rb') as file:
            file_data = {'file': (filename, file)}
            response = requests.post(url=upload_url, files=file_data)
            response.raise_for_status()

        os.remove(local_file_dir)

    upload(filename)


@shared_task
def update_file(filename):
    def update(filename):
        update_url = Endpoint.update
        local_file_dir = PATH_TO_LOCAL_STORAGE + filename

        with open(local_file_dir, 'rb') as file:
            file_data = {'file': (filename, file)}
            response = requests.post(url=update_url, files=file_data)
            response.raise_for_status()

        os.remove(local_file_dir)

    update(filename)


@shared_task
def remove_file(file_data):
    def remove(file_data):
        remove_url = Endpoint.remove
        response = requests.post(url=remove_url, json=file_data)
        response.raise_for_status()

    remove(file_data)
