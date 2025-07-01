from django.db import models
from django.utils.translation import gettext_lazy as _

from geant_examples.validators import title_not_verbose_view, validate_index_order
from users.models import User


class Example(models.Model):

    title_verbose = models.CharField(
        max_length=255, unique=True, blank=False, null=False)
    title_not_verbose = models.CharField(
        max_length=10, unique=True, validators=[title_not_verbose_view], blank=False, null=False)
    description = models.TextField(help_text=_(
        'Description of example'), blank=True)
    date_to_update = models.DateField(auto_now=True)
    tags = models.ManyToManyField('Tag', related_name='examples', blank=True, default=_(
        'Here can be description of example'))
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='examples'
    )
    synchronized = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Example")
        verbose_name_plural = _("Examples")

    def __str__(self):
        return self.title_not_verbose


class Command(models.Model):
    title = models.CharField(max_length=255)
    default = models.CharField(max_length=255)
    order_index = models.IntegerField(validators=[validate_index_order])
    example = models.ForeignKey(
        Example,
        on_delete=models.CASCADE,
        related_name='commands'
    )
    min = models.FloatField(null=True, blank=True)
    max = models.FloatField(null=True, blank=True)
    signature = models.CharField(max_length=255, null=True, blank=True)
    command_list = models.ForeignKey(
        'CommandList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='commands'
    )

    class Meta:
        verbose_name = _("Command")
        verbose_name_plural = _("Commands")
        ordering = (
            "order_index",
        )
        constraints = [
            models.UniqueConstraint(
                fields=["example", "order_index"],
                name="unique_constraint_index"
            )
        ]

    def __str__(self):
        return f"command {self.title} | example {self.example}"


class CommandList(models.Model):
    title = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = _("Command List")
        verbose_name_plural = _("Commands List")

    def __str__(self):
        return self.title


class CommandValue(models.Model):
    command_list = models.ForeignKey(
        CommandList,
        on_delete=models.CASCADE,
        related_name='command_values'
    )
    value = models.CharField(max_length=255)

    class Meta:
        verbose_name = _("Value for command list")
        verbose_name_plural = _("Values for command list")

    def __str__(self):
        return f"{self.value} for {self.command_list.title} command list"


class ExampleCommand(models.Model):
    users = models.ManyToManyField(
        User, related_name='example_commands', through='UserExampleCommand')
    key_s3 = models.CharField(
        max_length=255,
        help_text=_('in this field encoded all info about example'),
        unique=True
    )
    example = models.ForeignKey(
        Example,
        on_delete=models.CASCADE,
        related_name='example_commands'
    )

    class Meta:
        verbose_name = _('ExampleCommand')
        verbose_name_plural = _('ExampleCommands')

    def __str__(self):
        return self.key_s3


class UserExampleCommand(models.Model):
    class StatusChoice(models.IntegerChoices):
        executing = 0, _('In process')
        executed = 1, _('Completed')
        failure = 2, _('Executing failure')

    user = models.ForeignKey(User, on_delete=models.Case)
    example_command = models.ForeignKey(
        ExampleCommand, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)
    status = models.SmallIntegerField(
        choices=StatusChoice.choices,
        help_text=_('Current status of example executing'),
        default=StatusChoice.executing
    )

    class Meta:
        verbose_name = _("UserExampleCommand")
        verbose_name_plural = _("UsersExampleCommands")
        ordering = ('user', 'creation_date')

    def __str__(self):
        return str(self.creation_date) + f', status {self.status}'


class Tag(models.Model):
    title = models.CharField(
        max_length=255,
        unique=True
    )

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __str__(self):
        return self.title


class Category(models.Model):
    title = models.CharField(
        max_length=255,
        unique=True
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.title
