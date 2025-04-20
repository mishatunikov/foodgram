from django.contrib.auth.models import AbstractUser
from django.db import models

from users.consts import MAX_LENGTH_NAME


class CustomUser(AbstractUser):
    email = models.EmailField(verbose_name='Электронная почта')
    first_name = models.CharField(
        max_length=MAX_LENGTH_NAME, verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_NAME, verbose_name='Фамилия'
    )
    avatar = models.ImageField(upload_to='avatars', null=True, default=None)
    REQUIRED_FIELDS = [
        'email',
        'first_name',
        'last_name',
    ]

    class Meta:
        ordering = ('-date_joined',)

