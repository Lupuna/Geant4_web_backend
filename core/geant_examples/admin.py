from django.contrib import admin

from geant_examples.models import Example, UserExampleCommand, Tag, ExampleCommand


admin.site.register(UserExampleCommand)
admin.site.register(Tag)
admin.site.register(Example)
admin.site.register(ExampleCommand)
