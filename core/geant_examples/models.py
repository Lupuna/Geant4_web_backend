from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User


class Example(models.Model):
    title = models.CharField(max_length=255)
    key_s3 = models.CharField(
        max_length=255,
        help_text=_('in this field encoded all info about example'),
        unique=True
    )
    date_to_update = models.DateField(auto_now=True)
    users = models.ManyToManyField(User, related_name='examples', through='UserExample')
    tags = models.ManyToManyField('Tag', related_name='examples')

    class Meta:
        verbose_name = _("Example")
        verbose_name_plural = _("Examples")

    def __str__(self):
        return self.title


class UserExample(models.Model):
    user = models.ForeignKey(User, on_delete=models.Case, related_name='user_examples')
    example = models.ForeignKey(Example, on_delete=models.CASCADE, related_name='example_users')
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("UserExample")
        verbose_name_plural = _("UsersExamples")
        ordering = ('user', 'creation_date')

    def __str__(self):
        return self.creation_date


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
