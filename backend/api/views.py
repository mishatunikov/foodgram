from functools import lru_cache, partial

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import (
    Prefetch,
    OuterRef,
    Subquery,
    Case,
    When,
    Q,
    Exists,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
)
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS

from api import consts
from api.paginators import LimitPageNumberPagination
from foodgram.models import (
    User,
    Tag,
    Recipe,
    Ingredient,
    RecipeIngredient,
    Subscription,
)
from api.serializers import (
    UserSerializer,
    AvatarSerializer,
    PasswordSerializer,
    TagSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
)


class UserViewSet(
    ListModelMixin, RetrieveModelMixin, CreateModelMixin, GenericViewSet
):
    """Обработчик запросов на работу с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
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
            return queryset.annotate(is_subscribed=Exists(subscription))

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
        serializer = self.get_serializer(request.user, data=request.data)
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
            data={'message': message}, status=status.HTTP_404_NOT_FOUND
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data.get('new_password'))
        user.save()
        return Response(
            data={'message': consts.PASSWORD_UPDATED},
            status=status.HTTP_201_CREATED,
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
