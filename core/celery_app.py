import os
import time
import celery
from celery.schedules import crontab

from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = celery.Celery('core')
app.config_from_object('django.conf:settings')
app.conf.broker_url = settings.CELERY_BROKER_URL
app.autodiscover_tasks()

# app.conf.beat_schedule = {
#     'auto-delete-files': {
#         'task': 'geant_tests_storage.tasks.auto_delete',
#         'schedule': crontab(minute='*')
#     }
# }

# app.conf.timezone = 'UTC'
