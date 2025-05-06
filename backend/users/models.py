from django.contrib.auth.models import AbstractUser
from django.db import models

from users import consts


class CustomUser(AbstractUser):
    email = models.EmailField(verbose_name='электронная почта', unique=True)
    first_name = models.CharField(
        max_length=consts.MAX_LENGTH_NAME,
        verbose_name='имя',
    )
    last_name = models.CharField(
        max_length=consts.MAX_LENGTH_NAME,
        verbose_name='фамилия',
    )
    avatar = models.ImageField(
        upload_to='avatars',
        null=True,
        default=None,
        blank=True,
        verbose_name='аватар',
    )
    REQUIRED_FIELDS = [
        'email',
        'first_name',
        'last_name',
    ]

    class Meta:
        ordering = ('-date_joined',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
