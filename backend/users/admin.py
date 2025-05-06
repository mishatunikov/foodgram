from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from foodgram.models import Favorite, Purchase, Subscription, Recipe
from users.models import CustomUser


class FavoriteInline(admin.TabularInline):
    model = Favorite
    extra = 0

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipe')


class PurchaseInline(admin.TabularInline):
    model = Purchase
    extra = 0
    verbose_name_plural = 'Корзина покупок'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipe')


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 0
    fields = ('name', 'cooking_time')


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    fk_name = 'user'
    extra = 0

    verbose_name = 'подписка'
    verbose_name_plural = 'Подписки'

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related('user', 'following')
        )


class SubscriberInline(admin.TabularInline):
    model = Subscription
    fk_name = 'following'
    extra = 0

    verbose_name = 'подписчик'
    verbose_name_plural = 'Подписчики'

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related('following', 'user')
        )


class CustomAdmin(UserAdmin):
    """Модель пользователя в админке."""

    list_display = (
        'user_username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
    )
    list_editable = ('is_staff', 'is_active')
    search_fields = ('email', 'first_name')
    inlines = (
        RecipeInline,
        FavoriteInline,
        PurchaseInline,
        SubscriptionInline,
        SubscriberInline,
    )

    @admin.display(description='юзернейм', ordering='username')
    def user_username(self, obj):
        return obj.username


CustomAdmin.fieldsets += (('Extra Fields', {'fields': ('avatar',)}),)

admin.site.register(CustomUser, CustomAdmin)
