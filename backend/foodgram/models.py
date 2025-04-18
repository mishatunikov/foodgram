from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import ManyToManyField

from foodgram import consts

User = get_user_model()


class BaseCreatedAt(models):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class BaseName(models):
    name = models.CharField(
        max_length=consts.MAX_NAME_FIELD, verbose_name='Название'
    )

    class Meta:
        abstract = True
        ordering = ('name',)


class Tag(BaseName):
    slug = models.SlugField(
        max_length=consts.MAX_SLUG_LENGTH, verbose_name='Идентификатор'
    )

    class Meta(BaseName.Meta):
        pass


class Ingredient(BaseName):
    measure_unit = models.CharField(
        max_length=consts.MEASURE_UNIT_LENGTH, verbose_name='Единица измерения'
    )

    class Meta(BaseName.Meta):
        pass


class RecipeIngredient(models):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    count_ingredient = models.PositiveSmallIntegerField(
        verbose_name='Количество'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
    )


class Recipe(BaseCreatedAt, BaseName):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='recipes',
        default=None,
        null=True,
    )
    description = models.TextField(verbose_name='Описание')
    ingredients = ManyToManyField(
        Ingredient,
        through=RecipeIngredient,
        verbose_name='Ингредиенты',
    )
    tags = ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время готовки'
    )

    class Meta(BaseCreatedAt.Meta):
        default_related_name = 'recipes'
