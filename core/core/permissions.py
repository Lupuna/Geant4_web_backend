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


class BaseUserGroupPermission(BasePermission):
    group = None

    def has_permission(self, request, view):
        user = request.user

        if user.groups.filter(name=self.group).exists():
            return True
        else:
            return False


class IsEmployeePermission(BaseUserGroupPermission):
    group = 'Employees'


class InLimitedEmployeeGroupPermission(BaseUserGroupPermission):
    group = 'LimitedEmployeeGroup'
