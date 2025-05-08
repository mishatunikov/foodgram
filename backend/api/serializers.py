from re import fullmatch

from api import consts
from api.fields import Base64ImageField
from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator

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


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )


class UserWriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели Users."""

    password = serializers.CharField(
        required=True, validators=[validate_password], write_only=True
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def get_request(self):
        return self.context.get('request')

    def create(self, validated_data):
        password = validated_data.pop('password')
        instance = User(**validated_data)
        instance.set_password(password)
        instance.save()
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'following')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'following'),
            )
        ]

    def validate(self, attrs):
        if attrs['user'] == attrs['following']:
            raise ValidationError(detail=consts.NOT_FOLLOW_SELF)
        return attrs


class RecipeSimpleSerializer(serializers.ModelSerializer):
    """Сериализатор для выдачи данных о рецептах в упрощенном виде."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserWithRecipeSerializer(UserReadSerializer):
    """
    Сериализатор выдачи данных о пользователях вместе со связанными
    с ними рецептами.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField()

    class Meta(UserReadSerializer.Meta):
        fields = UserReadSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        query_params = self.context.get('request').query_params
        recipes_limit = query_params.get('recipes_limit')
        if recipes_limit and fullmatch(
            consts.RECIPES_LIMIT_PARAM_PATTERN, recipes_limit
        ):
            return RecipeSimpleSerializer(
                obj.recipes.all()[: int(recipes_limit)], many=True
            ).data
        return RecipeSimpleSerializer(obj.recipes, many=True).data


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class PasswordSerializer(serializers.Serializer):
    """Сериализатор для обработки манипуляций с паролем пользователя."""

    new_password = serializers.CharField(
        max_length=consts.MAX_LENGTH_PASSWORD,
        required=True,
        validators=[
            validate_password,
        ],
    )
    current_password = serializers.CharField(
        max_length=consts.MAX_LENGTH_PASSWORD,
        required=True,
    )

    def validate_current_password(self, password):
        user: User = self.context.get('request').user
        if user.check_password(password):
            return password
        raise ValidationError(
            detail=consts.CURRENT_PASSWORD_IS_WRONG,
            code=status.HTTP_400_BAD_REQUEST,
        )

    def validate(self, attrs):
        if attrs.get('new_password') == attrs.get('current_password'):
            raise ValidationError(
                detail=consts.NEW_PASSWORD_IS_ALREADY_USED,
                code=status.HTTP_400_BAD_REQUEST,
            )
        return attrs


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с таблицей Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializerMixin(serializers.ModelSerializer):
    """Миксин с базовым набором для работы с моделью Recipe."""

    # author = UserReadSerializer(
    #     read_only=True,
    # )
    author = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        ]

    def get_author(self, obj):
        user = self.context.get('request').user
        serializer_data = UserReadSerializer(obj.author).data
        if user.is_authenticated:
            is_subscribed = Subscription.objects.filter(
                user=self.context.get('request').user, following=obj.author
            ).exists()
            serializer_data.update({'is_subscribed': is_subscribed})
        return serializer_data


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с данными таблицы Ingredient"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientsReadSerializer(serializers.ModelSerializer):
    """Сериализатор предоставления ответа с информацией об ингредиентах."""

    id = serializers.IntegerField(required=True, source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        read_only=True, source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(RecipeSerializerMixin):
    """Сериализатор для модели Recipe."""

    ingredients = RecipeIngredientsReadSerializer(
        many=True, source='ingredient_amounts', read_only=True
    )
    tags = TagSerializer(read_only=True, many=True)
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta(RecipeSerializerMixin.Meta):
        fields = RecipeSerializerMixin.Meta.fields + [
            'is_favorited',
            'is_in_shopping_cart',
        ]


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Сериализатор для записи в БД информацию об ингредиентах."""

    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(
        required=True,
        validators=[
            MinValueValidator(consts.MIN_AMOUNT),
            MaxValueValidator(consts.MAX_AMOUNT),
        ],
    )

    def validate_id(self, input_id):
        ingredient = Ingredient.objects.filter(id=input_id)
        if ingredient.exists():
            return input_id
        raise ValidationError(detail=consts.INGREDIENT_DO_NOT_EXIST)


class RecipeWriteSerializer(RecipeSerializerMixin):
    """
    Сериализатор для создания новых и редактирования уже созданных рецептов.
    """

    ingredients = RecipeIngredientWriteSerializer(
        required=True, many=True, write_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        required=True, many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(required=True)

    class Meta(RecipeSerializerMixin.Meta):
        pass

    def validate_ingredients(self, data):
        if not data:
            raise ValidationError(detail=consts.INGREDIENTS_REQUIRED)

        ingredients_id = [ingredient.get('id') for ingredient in data]
        if len(ingredients_id) != len(set(ingredients_id)):
            raise ValidationError(detail=consts.RECIPE_INGREDIENTS_DUPLICATED)

        return data

    def validate_tags(self, data):
        if not data:
            raise ValidationError(detail=consts.TAGS_REQUIRED)
        if len(set(data)) != len(data):
            raise ValidationError(detail=consts.RECIPE_TAGS_DUPLICATED)
        return data

    def validate(self, attrs):
        if self.context.get('request').method == 'PATCH':
            requirement_fields = set(consts.RECIPE_REQUIRED_UPDATE_FIELD)
            provided_fields = set(attrs.keys())
            missing_fields = requirement_fields - provided_fields

            if missing_fields:
                raise ValidationError(
                    detail=f'{consts.RECIPE_UPDATE_REQUIRED_FIELDS}: '
                    f'{", ".join(missing_fields)}'
                )
        return attrs

    def create(self, validated_data):
        tags = validated_data.pop('tags')

        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.add(*tags)

        self.create_recipe_ingredients_relation(
            recipe=recipe, ingredients_data=ingredients_data
        )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.pop('name', instance.name)
        instance.image = validated_data.pop('image', instance.image)
        instance.text = validated_data.pop('text', instance.text)
        instance.cooking_time = validated_data.pop(
            'cooking_time', instance.cooking_time
        )
        instance.tags.set(validated_data.pop('tags', instance.tags.all()))
        ingredients_data = validated_data.pop('ingredients', None)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.create_recipe_ingredients_relation(
                recipe=instance, ingredients_data=ingredients_data
            )
        instance.save()
        return instance

    @staticmethod
    def create_recipe_ingredients_relation(
        recipe: Recipe, ingredients_data: dict
    ):
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_data.get('id')
            )

            RecipeIngredient.objects.create(
                ingredient=ingredient,
                recipe=recipe,
                amount=ingredient_data['amount'],
            )


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для с избранного."""

    class Meta:
        fields = ('user', 'recipe')
        model = Favorite
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
            )
        ]


class PurchaseSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок пользователей."""

    class Meta:
        fields = ('user', 'recipe')
        model = Purchase
        validators = [
            UniqueTogetherValidator(
                queryset=Purchase.objects.all(),
                fields=('user', 'recipe'),
            )
        ]
