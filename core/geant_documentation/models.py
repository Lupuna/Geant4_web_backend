from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models

from users.models import User


class Category(models.Model):
    title = models.CharField(unique=True, max_length=255)

    def __str__(self):
        return self.title


class Chapter(models.Model):
    title = models.CharField(unique=True, max_length=255)

    def __str__(self):
        return self.title


class Article(models.Model):
    title = models.CharField(unique=True, max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    users = models.ManyToManyField(User, related_name='articles', through='ArticleUser')

    def __str__(self):
        return self.title


class ArticleUser(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='chosen_articles')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_articles')

    class Meta:
        unique_together = (('article', 'user'), )

    def save(self, *args, **kwargs):
        self.counter_check()
        return super().save(*args, **kwargs)

    def counter_check(self):
        query = ArticleUser.objects.filter(user=self.user)
        if self.pk:
            query.exclude(pk=self.pk)
        if query.count() >= 8:
            raise ValidationError("Max chosen articles is 8.")


class Subscription(models.Model):
    title = models.CharField(max_length=255)
    subscription_order = models.PositiveSmallIntegerField()
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='subscriptions')

    class Meta:
        unique_together = (('article', 'subscription_order'), ('article', 'title'))
        ordering = ('subscription_order',)

    def __str__(self):
        return self.title


class Element(models.Model):

    class TypeChoice(models.TextChoices):
        TEXT = 'text', 'text'
        GRAPHIC = 'csv', 'graphic'
        IMAGE = 'webp', 'image'
        FORMULA = 'formula', 'formula'
        SUBSUBSCRIPTION = 'subsubscription', 'subsubscription'

    text = models.TextField(null=True, blank=True)
    element_order = models.PositiveSmallIntegerField()
    type = models.CharField(choices=TypeChoice.choices, default=TypeChoice.TEXT, max_length=15)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='elements')

    class Meta:
        unique_together = (('subscription', 'element_order'), )
        ordering = ('element_order',)

    @classmethod
    def _field_requirements(cls):
        return {
            cls.TypeChoice.TEXT: {'text': True},
            cls.TypeChoice.FORMULA: {'text': True},
            cls.TypeChoice.SUBSUBSCRIPTION: {'text': True},
            cls.TypeChoice.IMAGE: {'text': False},
            cls.TypeChoice.GRAPHIC: {'text': False},
        }

    def __str__(self):
        return self.type

    def clean(self):
        requirements = self._field_requirements().get(self.type, {})

        for field, expected in requirements.items():
            value = getattr(self, field, None)

            if expected is True and not value:
                raise ValidationError({field: f'{field.capitalize()} must be set when type is "{self.type}".'})
            elif expected is False and value:
                raise ValidationError({field: f'{field.capitalize()} must NOT be set when type is "{self.type}".'})


class File(models.Model):
    class FormatChoice(models.TextChoices):
        WEBP = 'webp', 'webp'
        CSV = 'csv', 'csv'

    uuid = models.UUIDField(default=uuid4)
    format = models.CharField(choices=FormatChoice.choices, default=FormatChoice.WEBP, max_length=4)
    element = models.ForeignKey(Element, on_delete=models.CASCADE, related_name='files')

    def __str__(self):
        return f'{self.uuid}.{self.format}'

    def save(self, *args, **kwargs):
        count = File.objects.filter(element=self.element).count()
        if count >= 8:
            raise ValidationError('Max files for element is 8')

        return super().save(*args, **kwargs)
