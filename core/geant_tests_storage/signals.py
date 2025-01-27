from django.contrib.auth.models import Group, Permission

from geant_tests_storage.permissions import version_permissions, test_result_permissions, test_result_file_permissions


def create_default_groups(sender, **kwargs):
    groups_data = [
        {
            'name': 'Employees',
            'permissions': version_permissions + test_result_permissions + test_result_file_permissions
        },
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
                    print(f"Permission with codename '{perm_codename}' not found.")