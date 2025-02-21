from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User

from geant_examples.validators import title_not_verbose_view


class Example(models.Model):
    class CategoryChoices(models.TextChoices):
        default = 'default', _('Default category')

    title = models.CharField(max_length=255)
    date_to_update = models.DateField(auto_now=True)
    users = models.ManyToManyField(
        User, related_name='examples', through='UserExample')
    tags = models.ManyToManyField('Tag', related_name='examples', blank=True)
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
        return self.title


class ExampleGeant(models.Model):
    title = models.CharField(
        max_length=10,
        help_text='Title format should be like: TSU_XX_00. Title will be selected automatically, after selecting FK'
    )
    key_s3 = models.CharField(
        max_length=255,
        help_text=_('in this field encoded all info about example'),
        unique=True
    )
    example = models.ForeignKey(
        Example,
        on_delete=models.CASCADE,
        related_name='examples_geant'
    )

    class Meta:
        verbose_name = _('ExampleGeant')
        verbose_name_plural = _('ExamplesGeant')

    def __str__(self):
        return self.key_s3


class ExamplesTitleRelation(models.Model):
    title_verbose = models.CharField(
        max_length=255,
        unique=True,
    )
    title_not_verbose = models.CharField(
        max_length=10,
        validators=[title_not_verbose_view],
        unique=True
    )

    class Meta:
        verbose_name = _("Possible meanings of Examples titles")
        verbose_name_plural = _("Possible meanings of Examples titles")
        ordering = ('title_not_verbose', )

    def __str__(self):
        return self.title_verbose


class UserExample(models.Model):
    class StatusChoice(models.IntegerChoices):
        executing = 0, _('In process')
        executed = 1, _('Completed')
        never_executed = 2, _('Examples was never executed')

    user = models.ForeignKey(User, on_delete=models.Case,
                             related_name='user_examples')
    example = models.ForeignKey(
        Example, on_delete=models.CASCADE, related_name='example_users')
    creation_date = models.DateTimeField(auto_now_add=True)
    status = models.SmallIntegerField(
        choices=StatusChoice.choices,
        help_text=_('Current status of example executing'),
        default=StatusChoice.never_executed
    )

    class Meta:
        verbose_name = _("UserExample")
        verbose_name_plural = _("UsersExamples")
        ordering = ('user', 'creation_date')

    def __str__(self):
        return str(self.creation_date)


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
