from typing import Optional
from uuid import uuid4

from django.db.models import Model

from foodgram import consts


def generate_identifier(max_length: Optional[int] = None) -> str:
    """
    Генерирует идентификатор.

    :param max_length: Длина идентификатора. По умолчанию ограничено 32 символами.
    :return: Идентификатор
    """

    identifier = uuid4().hex[:max_length]
    return identifier


def get_short_link_id(model: Model, field_name: str = 'short_link_id') -> str:
    """
    Генерирует id для короткого url объекта переданной модели.

    :param model: Модель, для которой должен быть сгенерирован идентификатор.
    :param field_name: Название поля модели, хранящий идентификатор. По умолчанию - 'short_link_id'.
    :return: Уникальный идентификатор для короткой ссылки
    """
    short_identifiers = model.objects.values_list(field_name, flat=True)
    new_identifier = generate_identifier(
        max_length=consts.MAX_SHORT_LINK_ID_LENGTH
    )

    while new_identifier in short_identifiers:
        new_identifier = generate_identifier(
            max_length=consts.MAX_SHORT_LINK_ID_LENGTH
        )

    return new_identifier


def get_link(*args, https: bool = True) -> str:
    """
    Генерирует ссылки исходя из входных данных.

    :param args: Составляющие URL, разделенные /.
    :param https: Булево значение. Если установлен False, ссылка будет формата http.
    :return: URL адрес
    """

    startswith = consts.HTTPS_STARTSWITH if https else consts.HTTP_STARTSWITH
    return f'{startswith}{"/".join(args)}/'
