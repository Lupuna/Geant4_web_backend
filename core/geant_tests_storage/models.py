from datetime import datetime
from uuid import uuid4

from django.utils.timezone import make_naive
from django.utils.translation import gettext_lazy as _
from django.db import models


class Version(models.Model):
    title = models.CharField(max_length=255)

    class Meta:
        verbose_name = _("Version")
        verbose_name_plural = _("Versions")

    def __str__(self):
        return self.title


class TestResult(models.Model):
    version = models.ForeignKey(Version, on_delete=models.SET_NULL, related_name='tests_results', null=True)
    title = models.CharField(max_length=255)
    date_to_update = models.DateField(auto_now=True)
    creation_date = models.DateField(auto_now_add=True)
    day_to_delete = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = _("TestResult")
        verbose_name_plural = _("TestsResults")

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        self.date_to_delete_validator()

    def date_to_delete_validator(self):
        if self.day_to_delete:
            if self.creation_date > self.day_to_delete:
                raise ValueError(_('The "day_to_delete" field must be later than "creation_date".'))
            if self.date_to_update >= self.day_to_delete:
                raise ValueError(_('The "day_to_delete" field must be later than "date_to_update".'))


class TestResultFile(models.Model):
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='files')

    class Meta:
        verbose_name = _("TestResultFile")
        verbose_name_plural = _("TestsResultsFiles")

    def __str__(self):
        return str(self.uuid)
