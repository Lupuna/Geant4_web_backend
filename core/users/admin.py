from django.contrib import admin

from users.models import User, Example, UserExample


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag', 'email')
    list_display_links = ('id', 'tag')


admin.site.register(Example)
admin.site.register(UserExample)
