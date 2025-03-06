from celery import shared_task

from . models import Version, TestResult, TestResultFile

from django.utils import timezone

from loguru import logger


@shared_task
def auto_delete():
    expired_versions = Version.objects.filter(
        day_to_delete__lte=timezone.now())
    expired_test_results = TestResult.objects.filter(
        day_to_delete__lte=timezone.now())
    expired_test_results_files = TestResultFile.objects.filter(
        day_to_delete__lte=timezone.now())

    deleted_versions_count = expired_versions.delete()
    deleted_test_results_count = expired_test_results.delete()
    deleted_test_results_files_count = expired_test_results_files.delete()

    logger.info(
        f'\n- Count of deleted expired versions: {deleted_versions_count[0]}\n- Count of deleted expired test_results: {deleted_test_results_count[0]}\n- Count of deleted expired test_results_files: {deleted_test_results_files_count[0]}')
