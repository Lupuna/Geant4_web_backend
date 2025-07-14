from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


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


@shared_task
def send_celery_mail_advanced(subject, message, recipients, html_template=None, context=None):
    if html_template and context:
        html_content = render_to_string(html_template, context)
        email = EmailMultiAlternatives(subject, message, to=recipients)
        email.attach_alternative(html_content, "text/html")
    else:
        email = EmailMultiAlternatives(subject, message, to=recipients)
    email.send()
