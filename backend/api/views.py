import io

from django.db.models import Count, Exists, OuterRef, Prefetch
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import (
    GenericViewSet,
    ModelViewSet,
    ReadOnlyModelViewSet,
)

from api import consts
from api.filters import DoubleSearchName, RecipeFilterSet
from api.paginators import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientsSerializer,
    PasswordSerializer,
    PurchaseSerializer,
    RecipeReadSerializer,
    RecipeSimpleSerializer,
    RecipeWriteSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserReadSerializer,
    UserWithRecipeSerializer,
    UserWriteSerializer,
)
from api.utils import create_pdf
from foodgram.models import (
    Favorite,
    Ingredient,
    Purchase,
    Recipe,
    RecipeIngredient,
    Subscription,
    Tag,
    User,
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
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        methods=['get'],
        permission_classes=[IsAuthenticated],
        detail=False,
        pagination_class=LimitPageNumberPagination,
    )
    def subscriptions(self, request):
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
            status=status.HTTP_201_CREATED,
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
                {'message': consts.NO_SUBSCRIPTION},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class TagViewSet(ReadOnlyModelViewSet):
    """Обработчик запросов к модели Tag."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):
    """Обработчик запросов к модели Recipe."""

    pagination_class = LimitPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)

    def get_serializer_class(self):

        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = Recipe.objects.prefetch_related(
            Prefetch(
                lookup='recipe_ingredients',
                queryset=RecipeIngredient.objects.select_related('ingredient'),
                to_attr='ingredient_amounts',
            ),
            'tags',
        ).select_related('author')
        if self.request.user.is_authenticated:
            return queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user, recipe=OuterRef('pk')
                    ),
                ),
                is_in_shopping_cart=Exists(
                    Purchase.objects.filter(
                        user=self.request.user, recipe=OuterRef('pk')
                    )
                ),
            )
        return queryset

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
        return Response(data={'short-link': recipe.get_short_url})

    @staticmethod
    def create_related_instance(serializer_class, pk, request):
        instance = get_object_or_404(Recipe, id=pk)
        serializer = serializer_class(
            data={'user': request.user.pk, 'recipe': instance.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            RecipeSimpleSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def delete_related_instance(
        related_model,
        pk,
        request,
        exist_error_message=consts.RELATED_INSTANCE_NOT_EXIST,
    ):
        if not Recipe.objects.filter(pk=pk).exists():
            raise NotFound()

        deleted, _ = related_model.objects.filter(
            user=request.user.id, recipe=pk
        ).delete()

        if not deleted:
            return Response(
                {'message': exist_error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True,
        methods=['post'],
        url_name='favorite',
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def favorite(self, request, pk):
        return self.create_related_instance(
            FavoriteSerializer, pk=pk, request=request
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return self.delete_related_instance(
            related_model=Favorite,
            pk=pk,
            exist_error_message=consts.RECIPE_IS_NOT_FAVORITE,
            request=request,
        )

    @action(
        methods=['post'],
        detail=True,
        url_name='purchase',
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def shopping_cart(self, request, pk):
        return self.create_related_instance(
            serializer_class=PurchaseSerializer,
            pk=pk,
            request=request,
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart_recipe(self, request, pk):
        return self.delete_related_instance(
            related_model=Purchase,
            pk=pk,
            request=request,
            exist_error_message=consts.RECIPE_NOT_IN_SHOPPING_CART,
        )

    @action(
        methods=['get'],
        detail=False,
        url_name='download_shopping_cart',
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def download_shopping_cart(self, request):
        user = request.user
        user_shopping_cart = user.purchase_list.all().values_list(
            'recipe_id', flat=True
        )
        queryset = self.get_queryset().filter(id__in=[*user_shopping_cart])
        ingredients = {}

        for recipe in queryset:
            for ingredients_amount in recipe.ingredient_amounts:
                ingredient = ingredients.get(
                    ingredients_amount.ingredient.name,
                )
                if ingredient:
                    ingredient['amount'] += ingredients_amount.amount

                else:
                    ingredients[ingredients_amount.ingredient.name] = {
                        'measurement_unit': (
                            ingredients_amount.ingredient.measurement_unit
                        ),
                        'amount': ingredients_amount.amount,
                    }

        sorted_ingredients = sorted(
            ingredients.items(),
            reverse=True,
            key=lambda x: x[1]['amount'],
        )
        list_for_file = [
            f'• {ing[0]} ({ing[1]["measurement_unit"]}) - {ing[1]["amount"]}'
            for ing in sorted_ingredients
        ]
        buffer = io.BytesIO()
        create_pdf(
            data=list_for_file,
            filename=buffer,
            header=consts.INGREDIENTS_FILE_HEADER,
        )
        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename='ingredients.pdf',
            content_type='application/pdf',
        )


class IngredientViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """Обработчик запросов к данным об ингредиентах."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DoubleSearchName,)
    search_fields = ('name',)
