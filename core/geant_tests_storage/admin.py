from django.contrib import admin
from django.contrib.auth.models import Group
from geant_tests_storage.models import Version, TestResult, TestResultFile, FileModeModel

admin.site.register(Version)
admin.site.register(TestResult)
admin.site.register(TestResultFile)
admin.site.register(FileModeModel)
admin.site.register(Group.user_set.through)
