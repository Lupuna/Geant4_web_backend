from django.core.validators import RegexValidator

no_at_validator = RegexValidator(
    regex=r'^[\w-]+$',
    code='invalid_char'
)
