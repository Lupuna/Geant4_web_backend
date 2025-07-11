import loguru
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from geant_examples.models import Example, Command, ExampleCommand
from geant_examples.models import UserExampleCommand
from users.documents import UserExampleCommandDocument
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


@receiver(m2m_changed, sender=ExampleCommand.users.through)
def update_user_example_command_document(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':

        for user_id in pk_set:
            try:
                us_ex_command = UserExampleCommand.objects.get(
                    user_id=user_id,
                    example_command=instance
                )
                UserExampleCommandDocument().update(us_ex_command, refresh=True)
                loguru.logger.critical(f'update for {user_id}, {instance}, {us_ex_command}')
            except UserExampleCommand.DoesNotExist:
                pass
