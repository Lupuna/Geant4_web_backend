from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from geant_examples.models import Example, Command
from utils.services import DatabaseSynchronizer

@receiver(post_save, sender=Command)
def save_command(sender, instance, **kwargs):
    sync = DatabaseSynchronizer(command=instance)
    sync.run()

@receiver(post_delete, sender=Command)
def delete_command(sender, instance, **kwargs):
    sync = DatabaseSynchronizer(command=instance)
    sync.run()

@receiver(post_delete, sender=Example)
def delete_example(sender, instance, **kwargs):
    sync = DatabaseSynchronizer(example=instance)
    sync.drop_example()









