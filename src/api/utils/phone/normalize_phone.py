import re

from django.core.exceptions import ValidationError


def normalize_phone(value):
    digits = re.findall(r'\d', value)
    if len(digits) != 12:
        raise ValidationError('Phone number must be at least 9 digits')
    return ''.join(digits)

