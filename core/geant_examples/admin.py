from django.contrib import admin

from geant_examples.models import Example, UserExample, Tag, ExampleGeant, ExamplesTitleRelation


admin.site.register(UserExample)
admin.site.register(Tag)
admin.site.register(ExamplesTitleRelation)
admin.site.register(Example)


@admin.register(ExampleGeant)
class ExampleGeantAdmin(admin.ModelAdmin):
    exclude = ('title', )
