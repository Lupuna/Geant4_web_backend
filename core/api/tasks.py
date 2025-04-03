from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_celery_mail(subject, message, from_email, recipient_list, auth_user, auth_password):
    send_mail(subject=subject,
              message=message,
              from_email=from_email,
              recipient_list=recipient_list,
              auth_user=auth_user,
              auth_password=auth_password)
