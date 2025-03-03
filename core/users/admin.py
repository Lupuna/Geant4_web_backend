from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag', 'email')
    list_display_links = ('id', 'tag')
