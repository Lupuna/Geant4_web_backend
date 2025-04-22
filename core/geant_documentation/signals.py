from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from file_client.documentation_image_client import DocumentationImageRenderClient
from file_client.example_csv_client import ExampleRendererClient
from file_client.tasks import destroy_documentation_image_task, destroy_documentation_graphic_task
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


@receiver(post_delete, sender=File)
def destroy_file(sender, instance, **kwargs):
    match instance.type:
        case 'webp':
            destroy_documentation_image_task.delay(name=str(instance.uuid))
        case 'csv':
            destroy_documentation_graphic_task.delay(name=str(instance.uuid))
        case _:
            pass