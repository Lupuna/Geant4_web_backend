from rest_framework.permissions import BasePermission


version_permissions = [
    'add_version', 'change_version',
    'delete_version', 'view_version'
]
test_result_permissions = [
    'add_testresult', 'change_testresult',
    'delete_testresult', 'view_testresult'
]
test_result_file_permissions = [
    'add_testresultfile', 'delete_testresultfile',
    'view_testresultfile'
]


class IsStaffPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if user.is_staff:
            return True
        else:
            return False


class GroupPermission(BasePermission):
    actions = {
        'GET': 'view',
        'POST': 'add',
        'PATCH': 'change',
        'PUT': 'change',
        'DELETE': 'delete'
    }

    def __init__(self, model: str, request_method: str, group_name=None):
        self._model = model
        self.request_method = request_method
        self._group_name = group_name

    @property
    def _perm_codename(self):
        model_name = self._model.lower()
        action = self.actions[self.request_method]

        return f'{action}_{model_name}'

    def has_permission(self, request, view):
        user = request.user

        if user.is_staff:
            return True

        codename = self._perm_codename

        if not self._group_name:
            user_groups = user.groups.prefetch_related('permissions')

            if not user_groups:
                return False

            access = any(map(lambda group: group if codename in group.permissions.values_list(
                'codename', flat=True) else None, user_groups))
        else:
            user_group = user.groups.prefetch_related(
                'permissions').filter(name=self._group_name).first()

            if not user_group:
                return False

            access = codename in user_group.permissions.values_list(
                'codename', flat=True)

        if access:
            return True

        return False
