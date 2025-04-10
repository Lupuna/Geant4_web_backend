import subprocess

from celery import shared_task
from django.conf import settings

@shared_task(name="utils.tasks.backup_database")
def backup_database():
    subprocess.run(
        ["python", "manage.py", "dumpdata", "--output" , "backup.json"]
    )
