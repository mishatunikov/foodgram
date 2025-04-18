from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import ManyToManyField

from foodgram import consts

User = get_user_model()


class BaseCreatedAt(models):
    """Абстрактная модель. Наделяет наследников автоматически генерируемым полем created_at."""

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class BaseName(models):
    """Абстрактная модель. Наделяет наследников полем name."""

    name = models.CharField(
        max_length=consts.MAX_NAME_FIELD, verbose_name='Название'
    )

    class Meta:
        abstract = True
        ordering = ('name',)


class Tag(BaseName):
    """Модель описывающая теги."""

    slug = models.SlugField(
        max_length=consts.MAX_SLUG_LENGTH,
        verbose_name='Идентификатор',
        db_index=True,
    )

    class Meta(BaseName.Meta):
        pass


class Ingredient(BaseName):
    """Модель описывающая ингредиенты."""

    measure_unit = models.CharField(
        max_length=consts.MEASURE_UNIT_LENGTH, verbose_name='Единица измерения'
    )

    class Meta(BaseName.Meta):
        pass


class RecipeIngredient(models):
    """Промежуточная модель для связи отношением многие ко многим модели Recipe и Ingredient."""

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
    """Модель описывающая рецепты"""

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


class Favorite(BaseCreatedAt):
    """Модель описывающие связь избранных пользователем рецептов."""

    user = models.ForeignKey(
        User, related_name='favorites', on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe, related_name='users_favorite', on_delete=models.CASCADE
    )

    class Meta(BaseCreatedAt.Meta):
        pass


class Subscription(BaseCreatedAt):
    """Модель описывающая связь пользователя с его подписчиками."""

    user = models.ForeignKey(
        User, related_name='subscribers', on_delete=models.CASCADE
    )
    subscriber = models.ForeignKey(
        User, related_name='subscriptions', on_delete=models.CASCADE
    )

    class Meta(BaseCreatedAt.Meta):
        pass
