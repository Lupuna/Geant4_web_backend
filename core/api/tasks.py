from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_celery_mail(topic, message, recipient_list):
    send_mail(
        subject=topic,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        auth_user=settings.EMAIL_HOST_USER,
        auth_password=settings.EMAIL_HOST_PASSWORD
    )
