import base64

from django.contrib.auth.password_validation import validate_password
from rest_framework import status
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

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


# class RecipeIngredientsSerializer(serializers.ModelSerializer):
#
#     id = serializers.IntegerField(required=True, source='ingredient.id')
#     name = serializers.ReadOnlyField(source='ingredient.name')
#     measurement_unit = serializers.ReadOnlyField(
#         read_only=True, source='ingredient.measurement_unit'
#     )
#
#     class Meta:
#         model = RecipeIngredient
#         fields = ('id', 'name', 'measurement_unit', 'amount')
#
#
# class RecipeReadSerializer(serializers.ModelSerializer):
#     """Сериализатор для модели Recipe."""
#
#     author = UserSerializer(read_only=True)
#     tags = serializers.PrimaryKeyRelatedField(
#         queryset=Tag.objects.all(), many=True, required=True
#     )
#     ingredients = RecipeIngredientsSerializer(
#         many=True, source='ingredient_amounts', read_only=True
#     )
#
#     class Meta:
#         model = Recipe
#         fields = (
#             'author',
#             'id',
#             'ingredients',
#             'tags',
#             'name',
#             'text',
#             'cooking_time',
#         )
