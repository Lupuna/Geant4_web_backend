from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User

from geant_examples.validators import title_not_verbose_view


class Example(models.Model):
    class CategoryChoices(models.TextChoices):
        default = 'default', _('Default category')

    title_verbose = models.CharField(
        max_length=255, unique=True, blank=False, null=True)
    title_not_verbose = models.CharField(
        max_length=10, unique=True, validators=[title_not_verbose_view], blank=False, null=True)
    description = models.TextField(help_text=_(
        'Description of example'), blank=True)
    date_to_update = models.DateField(auto_now=True)
    tags = models.ManyToManyField('Tag', related_name='examples', blank=True, default=_(
        'Here can be description of example'))
    category = models.CharField(
        max_length=255,
        choices=CategoryChoices.choices,
        default=CategoryChoices.default,
        help_text=_('Category of example')
    )

    class Meta:
        verbose_name = _("Example")
        verbose_name_plural = _("Examples")

    def __str__(self):
        return self.title_not_verbose


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
