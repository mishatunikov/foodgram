import base64

from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinValueValidator
from rest_framework import status
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api import consts
from foodgram.models import User, Tag, Recipe, Ingredient, RecipeIngredient


class Base64ImageField(serializers.ImageField):
    """Поле для обработки изображений, закодированных base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_img, imgstr = data.split(';base64,')
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'{self.context.get("request").user.username}.{format_img.split("/")[-1]}',
            )
            return data


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели Users."""

    password = serializers.CharField(
        required=True, validators=[validate_password], write_only=True
    )
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
            'password',
        )

    # def get_is_subscribed(self, obj):
    #     request = self.get_request()
    #     return request.user in obj.subscribers_for_user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.get_request()

        if request.method == 'POST':
            data.pop('avatar')
            data.pop('is_subscribed')

        return data

    def get_request(self):
        return self.context.get('request')

    def validate(self, attrs):
        return super().validate(attrs)

    def create(self, validated_data):
        password = validated_data.pop('password')
        instance = User(**validated_data)
        instance.set_password(password)
        instance.save()
        return instance


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

    author = UserSerializer(
        read_only=True,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )


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
    tags = serializers.SerializerMethodField()

    class Meta(RecipeSerializerMixin.Meta):
        pass

    def get_tags(self, obj):
        if self.context.get('view').action == 'retrieve':
            return TagSerializer(
                obj.tags.all(), read_only=True, many=True
            ).data
        return [tag.id for tag in obj.tags.all()]


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Сериализатор для записи в БД информацию об ингредиентах."""

    id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(
        required=True,
        validators=[
            MinValueValidator(1),
        ],
    )

    def validate_id(self, input_id):
        ingredient = Ingredient.objects.filter(id=input_id)
        if ingredient.exists():
            return input_id
        raise ValidationError(detail='Ингредиент с указанным id не найден.')


class RecipeWriteSerializer(RecipeSerializerMixin):
    """Сериализатор для создания новых и редактирования уже созданных рецептов."""

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
        serializer = RecipeIngredientWriteSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

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
