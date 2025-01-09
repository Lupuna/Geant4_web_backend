from django.contrib import admin

from geant_examples.models import Example, UserExample, Tag

admin.site.register(Example)
admin.site.register(UserExample)
admin.site.register(Tag)
