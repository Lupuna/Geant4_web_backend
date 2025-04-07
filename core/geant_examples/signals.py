import requests

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from loguru import logger

from .models import Example

@receiver(post_save, sender=Example)
def send_request_on_create(sender, instance, created, **kwargs):
    if created:
        url = settings.BACKEND_URL
        payload = {
            'title': instance.title_not_verbose,
        }
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(url, json=payload, headers=headers)
        except Exception as e:
            logger.error(str(e))
        else:
            logger.info(f"success create model on Backend Service. {response.status_code}")
