import os

from django.conf import settings

import requests


upload_url = settings.STORAGE_URL + "/upload/"
update_url = settings.STORAGE_URL + "/update/"
download_url = settings.STORAGE_URL + "/retrieve/"
remove_url = settings.STORAGE_URL + "/remove/"


def local_dir(file_data):
    filename = file_data.get('filename', None)

    if not filename:
        raise ValueError('File name was not provide')

    return settings.PATH_TO_LOCAL_STORAGE + filename


def file_exists(file_data):
    return os.path.exists(local_dir(file_data))


def download(file_data):
    if not file_exists(file_data):
        response = requests.post(url=download_url, json=file_data)
        response.raise_for_status()
        content_disposition = response.headers.get('Content-Disposition', None)

        if not content_disposition:
            raise ValueError('Cannot extract Content-Desposition from headers')

        out_file_name = content_disposition.split('filename=')[-1].strip('"')
        local_file_data = {'filename': out_file_name}
        local_file_dir = local_dir(local_file_data)

        with open(local_file_dir, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    else:
        raise ValueError('File already exists')


def send(file_data, update=False):
    if file_exists(file_data):
        local_file_dir = local_dir(file_data)
        filename = file_data.get('filename')

        with open(local_file_dir, 'rb') as file:
            data = {'file': (filename, file)}

            if update:
                response = requests.post(url=update_url, files=data)
            else:
                response = requests.post(url=upload_url, files=data)

            response.raise_for_status()

        os.remove(local_file_dir)
    else:
        raise ValueError('File does not exists')


def remove(file_data):
    response = requests.post(url=remove_url, json=file_data)
    response.raise_for_status()

    if file_exists(file_data):
        os.remove(local_dir(file_data))
