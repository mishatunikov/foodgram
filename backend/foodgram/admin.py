from django.contrib import admin
from django.db.models import Count, F, Value
from django.db.models.functions import Concat

from foodgram import consts
from foodgram.models import (
    Favorite,
    Ingredient,
    Purchase,
    Recipe,
    Subscription,
    Tag,
)


class IngredientRecipeInlineMixin(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 0


class NoAddMixin:
    """Убирает доступ к добалению объекта в админке."""

    def has_add_permission(self, request, obj=None):
        return False


class RecipeIngredientsInline(NoAddMixin, IngredientRecipeInlineMixin):

    fields = ('recipe',)
    readonly_fields = ('recipe',)
    verbose_name = 'рецепт'
    verbose_name_plural = 'Рецепты'
    can_delete = False


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Модель Ingredient в админке."""

    list_display = ('name', 'measurement_unit', 'count_using')
    readonly_fields = ('count_using',)
    search_fields = ('name',)
    inlines = (RecipeIngredientsInline,)

    def get_queryset(self, request):
        return Ingredient.objects.annotate(
            ingredients_in_recipe_count=Count(
                'recipe_ingredients', distinct=True
            )
        )

    @admin.display(
        description='Использования в рецептах',
        ordering='ingredients_in_recipe_count',
    )
    def count_using(self, obj):
        return obj.ingredients_in_recipe_count


class RecipeTagInline(NoAddMixin, admin.TabularInline):

    model = Recipe.tags.through
    extra = True
    readonly_fields = ('recipe', 'get_author')
    can_delete = False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipe__author')

    @admin.display(description='Автор рецепта')
    def get_author(self, obj):
        return obj.recipe.author


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Модель тегов в админке"""

    list_display = ('name', 'slug', 'count_recipes')
    inlines = (RecipeTagInline,)
    readonly_fields = ('count_recipes',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(recipe_count=Count('recipes'))
        )

    @admin.display(description='количество рецептов', ordering='recipe_count')
    def count_recipes(self, obj):
        return obj.recipe_count


class IngredientRecipeInline(IngredientRecipeInlineMixin):

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related('ingredient')
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Модель рецептов в админке."""

    inlines = (IngredientRecipeInline,)
    list_display = (
        'name',
        'author_name',
        'short_text',
        'cooking_time',
        'count_favorite',
        'count_in_purchase',
    )
    search_fields = ('name', 'author_fullname')
    filter_horizontal = ('tags',)
    list_filter = ('tags',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related('author')
        return queryset.annotate(
            favorite_count=Count('users_favorite', distinct=True),
            purchase_count=Count('users_purchase', distinct=True),
            author_fullname=Concat(
                F('author__first_name'),
                Value(' '),
                F('author__last_name'),
            ),
        )

    @admin.display(description='Полное имя автора')
    def author_name(self, obj):
        return obj.author_fullname

    @admin.display(description='сокращенное описание')
    def short_text(self, obj):
        words = obj.text.split()
        shortened_text = ' '.join(words[: consts.ADMIN_PANEL_MAX_WORDS])
        if len(words) > consts.ADMIN_PANEL_MAX_WORDS:
            shortened_text += '...'
        return shortened_text

    @admin.display(description='количество лайков', ordering='favorite_count')
    def count_favorite(self, obj):
        return obj.favorite_count

    @admin.display(
        description='добавлений в корзину', ordering='purchase_count'
    )
    def count_in_purchase(self, obj):
        return obj.purchase_count


class FavoritePurchaseMixin(admin.ModelAdmin):

    list_display = (
        'recipe',
        'user',
    )
    search_fields = ('user__username', 'recipe__name')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recipe')


@admin.register(Favorite)
class FavoriteAdmin(FavoritePurchaseMixin):
    """Модель избранное в админке."""


@admin.register(Purchase)
class PurchaseAdmin(FavoritePurchaseMixin):
    """Модель покупок в админке."""


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Модель подписок в админке."""

    list_display = ('description', 'user', 'following')
    search_fields = ('user__username', 'following__username')

    @admin.display(description='описание')
    def description(self, obj):
        return str(obj)

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related('user', 'following')
        )
