from django.contrib.auth.models import PermissionsMixin, Group
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from django.db import models, transaction
from uuid import uuid4

from core.validators import no_at_validator
from users.managers import UserManager

from autoslug import AutoSlugField


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        _('email filed'),
        unique=True,
        blank=False,
        db_index=True,
    )
    username = models.CharField(
        max_length=200,
        unique=True,
        validators=[
            no_at_validator,
        ]
    )
    tag = AutoSlugField(populate_from='username', unique=True)

    uuid = models.UUIDField(default=uuid4)
    is_employee = models.BooleanField(default=False)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_(
            "Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_email_verified = models.BooleanField(
        _("email verification status"),
        default=False,
        help_text=_(
            "For sending messages into email need to verificate email adress")
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    first_name = models.CharField()
    last_name = models.CharField()

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['tag', 'email']

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.tag

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_employee:
            self.add_employee_in_employee_group()

    def add_employee_in_employee_group(self):
        try:
            employee_group = Group.objects.get(name="Employees")
            self.groups.add(employee_group)
        except ObjectDoesNotExist:
            print('Group Employees not eyt')

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)
