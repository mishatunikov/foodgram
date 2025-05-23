from config import config
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import ManyToManyField

from foodgram import consts
from foodgram.consts import MAX_SHORT_LINK_ID_LENGTH
from foodgram.utils import get_link, get_short_link_id

User = get_user_model()


class BaseCreatedAt(models.Model):
    """
    Абстрактная модель. Наделяет наследников автоматически генерируемым полем
    created_at.
    """

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

    def __str__(self):
        return self.name


class Tag(BaseName):
    """Модель описывающая теги."""

    slug = models.SlugField(
        max_length=consts.MAX_SLUG_LENGTH,
        verbose_name='Идентификатор',
        unique=True,
        db_index=True,
    )

    class Meta(BaseName.Meta):
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'


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
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class RecipeIngredient(models.Model):
    """
    Промежуточная модель для связи отношением многие ко многим модели Recipe
    и Ingredient.
    """

    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(consts.MIN_AMOUNT_INGREDIENT),
            MaxValueValidator(consts.MAX_AMOUNT_INGREDIENT),
        ],
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
    )

    class Meta:
        default_related_name = 'recipe_ingredients'
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient_recipe',
            )
        ]


class Recipe(BaseCreatedAt, BaseName):
    """Модель описывающая рецепты"""

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='автор'
    )
    image = models.ImageField(upload_to='recipes', verbose_name='изображение')
    text = models.TextField(verbose_name='Описание')
    ingredients = ManyToManyField(
        Ingredient,
        through=RecipeIngredient,
        verbose_name='Ингредиенты',
    )
    tags = ManyToManyField(Tag, verbose_name='Теги', related_name='recipes')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время готовки',
        validators=[
            MinValueValidator(consts.MIN_COOKING_TIME),
            MaxValueValidator(consts.MAX_COOKING_TIME),
        ],
    )
    short_link_id = models.CharField(
        unique=True,
        max_length=MAX_SHORT_LINK_ID_LENGTH,
        blank=True,
        verbose_name='id короткой ссылки',
        help_text='генерируется автоматически',
    )

    class Meta(BaseCreatedAt.Meta):
        default_related_name = 'recipes'
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

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
        User,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='владелец избранного',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='users_favorite',
        on_delete=models.CASCADE,
        verbose_name='избранный рецепт',
    )

    class Meta(BaseCreatedAt.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_favorite'
            ),
        ]
        verbose_name = 'понравившийся рецепт'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return self.recipe.name


class Purchase(BaseCreatedAt):
    """Модель описывающая рецепты, добавленные пользователем в покупки."""

    user = models.ForeignKey(
        User,
        related_name='purchase_list',
        on_delete=models.CASCADE,
        verbose_name='владелец корзины покупок',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='users_purchase',
        on_delete=models.CASCADE,
        verbose_name='рецепт в корзине покупок',
    )

    class Meta(BaseCreatedAt.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_shopping_cart_recipe',
            ),
        ]
        verbose_name = 'корзина покупок'
        verbose_name_plural = 'корзины покупок'

    def __str__(self):
        return self.recipe.name
