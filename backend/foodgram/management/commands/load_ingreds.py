import csv
import json
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from foodgram.models import Ingredient

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


def load_data(file_path):
    """Считывает данные из файла и загружает их в таблицу Ingredient."""

    with open(BASE_DIR / file_path, 'r', encoding='utf-8') as file:
        ingredients = []
        if file_path.endswith('.csv'):
            reader = csv.reader(file, delimiter=',')
            for name, measure_unit in reader:
                ingredients.append(
                    Ingredient(name=name, measurement_unit=measure_unit)
                )
        if file_path.endswith('.json'):
            reader = json.load(file)
            for data in reader:
                ingredients.append(Ingredient(**data))

        Ingredient.objects.bulk_create(ingredients)


class Command(BaseCommand):
    """
    Команда для заполнения таблицы Ingredient данными из фалов .csv или .json.
    """

    help = (
        'Загружает данные для таблицы Ingredient из csv или json.'
        'ВАЖНО: '
        'Каждый файл должен включать в себя только название продукта и '
        'единицу измерения для него. При загрузке из csv, в качестве '
        'разделителя, должна использоваться запятая. '
        'JSON должен включать в себя только поля "name" и "measurement_unit". '
        'При выполнении команды нужно указать путь до файла относительно '
        'КОРНЯ ПРОЕКТА.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к файлу относительно корня проекта.',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            load_data(file_path)

        except FileNotFoundError as e:
            raise CommandError(str(e)) from e

        except Exception as e:
            raise CommandError(f'Ошибка при импорте данных: {str(e)}')

        else:
            sys.stdout.write(
                self.style.SUCCESS('Загрузка данных прошла успешно.')
            )
