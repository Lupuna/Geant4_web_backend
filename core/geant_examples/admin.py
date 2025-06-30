from django.contrib import admin

from geant_examples.models import Example, UserExampleCommand, Tag, ExampleCommand, Command, CommandValue, CommandList


admin.site.register(UserExampleCommand)
admin.site.register(Tag)
admin.site.register(Example)
admin.site.register(ExampleCommand)
admin.site.register(Command)
admin.site.register(CommandValue)
admin.site.register(CommandList)
