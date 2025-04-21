from django.db.models.signals import post_save
from django.dispatch import receiver

from geant_documentation.models import Element, File


@receiver(post_save, sender=Element)
def create_required_file(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.type in File.FormatChoice.values:
        File.objects.create(
            format=instance.type,
            element=instance
        )
