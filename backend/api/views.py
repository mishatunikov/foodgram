from functools import lru_cache

from django.db.models import (
    Prefetch,
    OuterRef,
    Subquery,
    Case,
    When,
    Q,
    Exists,
    Count,
)
from django.db.models.functions import Lower
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
)
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.filters import SearchFilter

from api import consts
from api.paginators import LimitPageNumberPagination
from foodgram.models import (
    User,
    Tag,
    Recipe,
    Ingredient,
    RecipeIngredient,
    Subscription,
    Favorite,
)
from api.serializers import (
    AvatarSerializer,
    PasswordSerializer,
    TagSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    SubscriptionSerializer,
    UserWithRecipeSerializer,
    UserReadSerializer,
    UserWriteSerializer,
    IngredientsSerializer,
    RecipeSimpleSerializer,
    FavoriteSerializer,
)


class UserViewSet(
    ListModelMixin, RetrieveModelMixin, CreateModelMixin, GenericViewSet
):
    """Обработчик запросов на работу с пользователями."""

    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all()

        if not user.is_authenticated:
            return queryset

        else:
            subscription = Subscription.objects.filter(
                user=self.request.user, following=OuterRef('pk')
            )
            return queryset.annotate(
                is_subscribed=Exists(subscription),
                recipes_count=Count('recipes'),
            ).order_by('-date_joined')

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return UserReadSerializer
        return UserWriteSerializer

    @action(
        methods=['get'],
        detail=False,
        url_name='me',
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['put'],
        detail=False,
        url_name='manage_avatar',
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
        serializer_class=AvatarSerializer,
    )
    def update_avatar(self, request):
        serializer = AvatarSerializer(
            request.user, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        user: User = request.user
        if user.avatar:
            user.avatar = None
            user.save()
            message = consts.AVATAR_DELETED
        else:
            message = consts.AVATAR_NOT_INSTALLED
        return Response(
            data={'message': message}, status=status.HTTP_204_NO_CONTENT
        )

    @action(
        methods=['post'],
        url_name='set_password',
        permission_classes=[IsAuthenticated],
        detail=False,
        serializer_class=PasswordSerializer,
    )
    def set_password(self, request):
        user: User = request.user
        serializer = PasswordSerializer(
            data=request.data, context={'request': self.request}
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data.get('new_password'))
        user.save()
        return Response(
            data={'message': consts.PASSWORD_UPDATED},
            status=status.HTTP_201_CREATED,
        )

    @action(
        methods=['get'],
        permission_classes=[IsAuthenticated],
        detail=False,
        pagination_class=LimitPageNumberPagination,
    )
    def subscription(self, request):
        user_subscriptions = (
            self.get_queryset()
            .prefetch_related()
            .filter(is_subscribed=True)
            .order_by('-subscribers__created_at')
        )
        page = self.paginate_queryset(queryset=user_subscriptions)
        serializer = UserWithRecipeSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post'],
        detail=True,
        url_name='subscribe',
        serializer_class=SubscriptionSerializer,
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def subscribe(self, request, pk):

        if not User.objects.filter(id=pk).exists():
            raise NotFound()

        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'following': pk},
            context={'request': self.request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        subscription_object = get_object_or_404(self.get_queryset(), id=pk)
        return Response(
            UserWithRecipeSerializer(
                subscription_object, context=serializer.context
            ).data,
            status=status.HTTP_200_OK,
        )

    @subscribe.mapping.delete
    def delete_subscription(self, request, pk):
        get_object_or_404(User, id=pk)

        if not (
            subscription := Subscription.objects.filter(
                user=request.user.id, following=pk
            )
        ).exists():
            return Response(
                {'message': 'Нет подписки на данного пользователя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription.delete()
        return Response(
            data={'message': consts.SUBSCRIPTION_DELETED},
            status=status.HTTP_204_NO_CONTENT,
        )


class TagViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """Обработчик запросов к модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):
    """Обработчик запросов к модели Recipe."""

    queryset = Recipe.objects.all()

    # Переопределение get_serializer_class плодит дополнительные запросы к БД.
    # Я не совсем понимаю почему так, есть догадки, что это связано с вложенными сериализаторами.
    # А если кэшировать, то дополнительных запросов не будет. Был бы рад пояснению, почему так и как лучше.
    @lru_cache()
    def get_serializer_class(self):

        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        return Recipe.objects.prefetch_related(
            Prefetch(
                lookup='recipe_ingredients',
                queryset=RecipeIngredient.objects.all().select_related(
                    'ingredient'
                ),
                to_attr='ingredient_amounts',
            ),
            'tags',
        ).select_related('author')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        object_with_info = self.get_queryset().get(id=serializer.instance.id)
        read_serializer = RecipeReadSerializer(
            object_with_info, context=self.get_serializer_context()
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = RecipeReadSerializer(
            self.get_queryset().get(id=instance.id),
            context=self.get_serializer_context(),
        )
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link',
        url_name='recipe_short_link',
    )
    def get_link(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        return Response(data={'short_link': recipe.get_short_url})

    @action(
        detail=True,
        methods=['post'],
        url_name='favorite',
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = FavoriteSerializer(
            data={'user': request.user.pk, 'recipe': recipe.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            RecipeSimpleSerializer(recipe).data, status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        if not Recipe.objects.filter(pk=pk).exists():
            raise NotFound()

        if not (
            favorite := Favorite.objects.filter(
                user=request.user.id, recipe=pk
            )
        ).exists():
            return Response(
                {'message': consts.RECIPE_IS_NOT_FAVORITE},
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite.delete()
        return Response(
            data={'message': consts.SUBSCRIPTION_DELETED},
            status=status.HTTP_204_NO_CONTENT,
        )


class IngredientViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """Обработчик запросов к данным об ингредиентах."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
