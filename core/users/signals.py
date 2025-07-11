from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from geant_examples.models import UserExampleCommand
from users.documents import UserExampleCommandDocument


@receiver(post_save, sender=UserExampleCommand)
def update_document(sender, instance, **kwargs):
    UserExampleCommandDocument().update(instance)

@receiver(post_delete, sender=UserExampleCommand)
def delete_document(sender, instance, **kwargs):
    UserExampleCommandDocument().delete(instance)