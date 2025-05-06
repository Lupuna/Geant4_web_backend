from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from geant_examples.models import Example
from utils.services import DatabaseSynchronizer


@receiver(post_save, sender=Example)
def save_example(sender, instance, created, **kwargs):
    if not created and instance.synchronized:
        sync = DatabaseSynchronizer(example=instance)
        sync.run()


@receiver(post_delete, sender=Example)
def delete_example(sender, instance, **kwargs):
    sync = DatabaseSynchronizer(example=instance)
    sync.drop_example()
