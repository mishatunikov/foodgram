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
        default='',
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


class Subscription(models.Model):
    """Модель описывающая связь пользователя с его подписчиками."""

    user = models.ForeignKey(
        CustomUser,
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='пользователь',
    )
    following = models.ForeignKey(
        CustomUser,
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='подписка',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'], name='unique_user_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='not_follow_self',
            ),
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return consts.SUBSCRIPTION_STR(
            self.user.username, self.following.username
        )
