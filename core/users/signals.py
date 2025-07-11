from django.db.models.signals import post_save
from django.dispatch import receiver

from geant_examples.models import UserExampleCommand
from users.documents import UserExampleCommandDocument


@receiver(post_save, sender=UserExampleCommand)
def update_document(sender, instance, **kwargs):
    from loguru import logger
    logger.info(f"SIGNAL: Обновление индекса для UserExampleCommand id={instance.pk} началось для user={instance.user}")
    UserExampleCommandDocument().update(instance)
    logger.info(f"SIGNAL: Обновление индекса для UserExampleCommand id={instance.pk} закончилось для user={instance.user}")