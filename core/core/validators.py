from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

no_at_validator = RegexValidator(
    regex=r'^[\w-]+$',
    message=_("The '@' symbol is not allowed"),
    code='invalid_char'
)
