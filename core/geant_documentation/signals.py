from django.db.models.signals import post_delete
from django.dispatch import receiver

from file_client.tasks import destroy_documentation_image_task, destroy_documentation_graphic_task
from geant_documentation.models import File


@receiver(post_delete, sender=File)
def destroy_file(sender, instance, **kwargs):
    match instance.format:
        case 'webp':
            destroy_documentation_image_task.delay(name=str(instance.uuid))
        case 'csv':
            destroy_documentation_graphic_task.delay(name=str(instance.uuid))
        case _:
            pass
