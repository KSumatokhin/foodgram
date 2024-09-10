from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from foodgram_backend.constants import (MAX_EMAIL, MAX_NAME)
from users.validators import validate_me


class MyUser(AbstractUser):
    username = models.CharField(
        max_length=MAX_NAME,
        unique=True,
        verbose_name='Имя пользователя',
        validators=[validate_me, UnicodeUsernameValidator()]
    )
    email = models.EmailField(
        max_length=MAX_EMAIL,
        unique=True
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars/',
        null=True,
        default=None
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'

    def __str__(self):
        return self.username
