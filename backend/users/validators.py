from django.core.exceptions import ValidationError

from foodgram_backend.constants import ME


def validate_me(value):
    if value.lower() == ME:
        raise ValidationError(f'Имя пользователя {value} запрещено!')
    return value
