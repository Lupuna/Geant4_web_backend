from django.contrib.auth.models import Group, Permission
from django.db.models import Q



custom_models = ['example', 'examplecommand', ]
query_filter = Q()
for model in custom_models:
    query_filter |= Q(codename__endswith=model)
perm_codenames = Permission.objects.filter(
    query_filter).values_list('codename', flat=True)


def create_default_groups(sender, **kwargs):
    groups_data = [
        {
            'name': 'Employees',
            'permissions': perm_codenames
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
