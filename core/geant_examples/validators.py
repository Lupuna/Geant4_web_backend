import re


def title_not_verbose_view(title):
    pattern = r'^TSU_[0-9]{2,3}$'

    if not bool(re.match(pattern, title)):
        raise ValueError('Value should look like this: TSU_00')
