import re
from django.core.exceptions import ValidationError


def title_not_verbose_view(value):
    pattern = r'^TSU_\d{2,3}$'

    if not re.match(pattern, str(value)):
        raise ValidationError('Value should look like this: TSU_00')
