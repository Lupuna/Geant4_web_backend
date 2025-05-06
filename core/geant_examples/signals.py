from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from geant_examples.models import Example, Command
from utils.services import DatabaseSynchronizer


@receiver(post_save, sender=Example)
def save_example(sender, instance, created, **kwargs):
    if not created and instance.synchronized:
        sync = DatabaseSynchronizer(example=instance)
        sync.run()

        
@receiver(post_save, sender=Command)
def save_command(sender, instance, created, **kwargs):
    example = instance.example
    example.synchronized = False
    example.save()

    
@receiver(post_delete, sender=Example)
def delete_example(sender, instance, **kwargs):
    sync = DatabaseSynchronizer(example=instance)
    sync.drop_example()


@receiver(post_delete, sender=Command)
def delete_command(sender, instance, **kwargs):
    example = instance.example
    example.synchronized = False
    example.save()
