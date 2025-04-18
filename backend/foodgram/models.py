from django.db import models
from django.contrib.auth import get_user_model

from foodgram import consts

User = get_user_model()


class Tag(models):
    name = models.CharField(
        max_length=consts.MAX_NAME_FIELD, verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=consts.MAX_SLUG_LENGTH, verbose_name='Идентификатор'
    )


class Ingredient(models):
    name = models.CharField(
        max_length=consts.MAX_SLUG_LENGTH, verbose_name='Название'
    )
    measure_unit = models.CharField(
        max_length=consts.MEASURE_UNIT_LENGTH, verbose_name='Единица измерения'
    )


class RecipeIngredient(models):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    count_ingredient = models.SmallIntegerField(verbose_name='Количество')
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)


class Recipe(models):
    pass
