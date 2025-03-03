from django.contrib import admin
from geant_tests_storage.models import Version, TestResult, TestResultFile

admin.site.register(Version)
admin.site.register(TestResult)
admin.site.register(TestResultFile)
