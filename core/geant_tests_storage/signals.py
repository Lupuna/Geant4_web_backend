from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.dispatch import receiver

from geant_tests_storage.models import FileModeModel

from core.permissions import version_permissions, test_result_permissions, test_result_file_permissions


def create_default_groups(sender, **kwargs):
    groups_data = [
        {
            'name': 'Employees',
            'permissions': version_permissions + test_result_permissions + test_result_file_permissions
        }
    ]

    for data in groups_data:
        group, created = Group.objects.get_or_create(name=data['name'])
        if created:
            group.save()
            for perm_codename in data['permissions']:
                try:
                    permission = Permission.objects.get(codename=perm_codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    print(
                        f"Permission with codename '{perm_codename}' not found.")


@receiver(post_save, sender=FileModeModel)
def remove_perms(sender, instance, **kwargs):
    employees_group = Group.objects.filter(
        name='Employees').prefetch_related('permissions').first()

    if instance.mode == FileModeModel.ModeChoice.any_employees_only:
        employees_group.permissions.clear()
    elif instance.mode == FileModeModel.ModeChoice.employees_only:
        perms_codenames = version_permissions + \
            test_result_file_permissions + test_result_permissions
        perms = Permission.objects.filter(codename__in=perms_codenames)
        employees_group.permissions.set(perms)
