from django.contrib import admin
from django.contrib.auth.models import Group, Permission

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag', 'email')
    list_display_links = ('id', 'tag')


admin.site.register(User.groups.through)
admin.site.register(Permission)
admin.site.register(Group.permissions.through)
