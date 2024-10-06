from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import F, Q

from foodgram_backend.constants import MAX_EMAIL, MAX_NAME
from users.validators import validate_me


class MyUser(AbstractUser):
    username = models.CharField(
        max_length=MAX_NAME,
        unique=True,
        verbose_name='Логин',
        validators=[validate_me, UnicodeUsernameValidator()]
    )
    email = models.EmailField(
        max_length=MAX_EMAIL,
        unique=True
    )
    first_name = models.CharField(
        max_length=MAX_NAME,
        verbose_name='Имя пользователя',
    )
    last_name = models.CharField(
        max_length=MAX_NAME,
        verbose_name='Фамилия пользователя',
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='users',
        null=True,
        default=None
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name='subscriptions'
    )
    author = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name='followers'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='except_self'
            )
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username}-{self.author.username}'
