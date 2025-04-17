from django.db import models
from django.contrib.auth import get_user_model

from foodgram.consts import MAX_NAME_FIELD, MAX_SLUG_LENGTH

User = get_user_model()


class Tag(models):
    name = models.CharField(max_length=MAX_NAME_FIELD, verbose_name='Название')
    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH, verbose_name='Идентификатор'
    )


class Recipe(models):
    pass
