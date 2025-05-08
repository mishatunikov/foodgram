import base64
from re import fullmatch

from api import consts
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class Base64ImageField(serializers.ImageField):
    """Поле для обработки изображений, закодированных base64."""

    def to_internal_value(self, data):
        if not isinstance(data, str) or not fullmatch(
            consts.BASE64_IMAGE_PATTERN, data
        ):
            raise ValidationError(detail=consts.BASE64_IMAGE_ERROR)

        format_img, imgstr = data.split(';base64,')
        return ContentFile(
            base64.b64decode(imgstr),
            name=f'{self.context.get("request").user.username}.'
            f'{format_img.split("/")[-1]}',
        )
