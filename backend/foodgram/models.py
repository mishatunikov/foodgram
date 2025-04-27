from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import ManyToManyField

from foodgram import consts
from foodgram.consts import MAX_SHORT_LINK_ID_LENGTH
from foodgram.utils import get_short_link_id, get_link
from config import config

User = get_user_model()


class BaseCreatedAt(models.Model):
    """Абстрактная модель. Наделяет наследников автоматически генерируемым полем created_at."""

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class BaseName(models.Model):
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
        unique=True,
        db_index=True,
    )

    class Meta(BaseName.Meta):
        pass


class Ingredient(models.Model):
    """Модель описывающая ингредиенты."""

    name = models.CharField(
        max_length=consts.MAX_NAME_FIELD,
        verbose_name='Название',
        db_index=True,
    )

    measurement_unit = models.CharField(
        max_length=consts.MEASURE_UNIT_LENGTH, verbose_name='Единица измерения'
    )

    class Meta(BaseName.Meta):
        ordering = ('id',)


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи отношением многие ко многим модели Recipe и Ingredient."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(verbose_name='Количество')
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
    )

    class Meta:
        default_related_name = 'recipe_ingredients'


class Recipe(BaseCreatedAt, BaseName):
    """Модель описывающая рецепты"""

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='recipes',
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = ManyToManyField(
        Ingredient,
        through=RecipeIngredient,
        verbose_name='Ингредиенты',
    )
    tags = ManyToManyField(Tag, verbose_name='Теги', related_name='recipes')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время готовки'
    )
    short_link_id = models.CharField(
        unique=True,
        max_length=MAX_SHORT_LINK_ID_LENGTH,
        blank=True,
    )

    class Meta(BaseCreatedAt.Meta):
        default_related_name = 'recipes'

    def save(self, *args, **kwargs):
        self.short_link_id = get_short_link_id(Recipe)
        super().save(*args, **kwargs)

    @property
    def get_short_url(self):
        return get_link(
            config.host.domain_name,
            consts.SHORT_URL_ENDPOINT,
            self.short_link_id,
            https=False,
        )


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
        User, related_name='subscriptions', on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User, related_name='subscribers', on_delete=models.CASCADE
    )

    class Meta(BaseCreatedAt.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'], name='unique_user_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='not_follow_self',
            ),
        ]


class Purchase(BaseCreatedAt):
    """Модель описывающая рецепты, добавленные пользователем в покупки."""

    user = models.ForeignKey(
        User, related_name='purchase_list', on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe, related_name='users_purchase', on_delete=models.CASCADE
    )

    class Meta(BaseCreatedAt.Meta):
        pass
