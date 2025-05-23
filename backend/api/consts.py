MAX_LENGTH_PASSWORD = 128
DEFAULT_PAGE_SIZE = 6
MAX_AMOUNT = 10_000
MIN_AMOUNT = 1

# Response messages
AVATAR_DELETED = 'Аватар успешно удален.'
AVATAR_NOT_INSTALLED = 'В текущем профиле аватар не установлен.'
PASSWORD_UPDATED = 'Пароль успешно обновлен.'
SUBSCRIPTION_DELETED = 'Подписка успешно отменена.'
RECIPE_IS_NOT_FAVORITE = 'Рецепт раннее не был добавлен в избранное.'
RECIPE_NOT_IN_SHOPPING_CART = 'Рецепт ранее не был добавлен в список покупок.'
RELATED_INSTANCE_NOT_EXIST = 'Связанный объект не существует.'
NO_SUBSCRIPTION = 'Нет подписки на данного пользователя'

# Validation error messages
NEW_PASSWORD_IS_ALREADY_USED = 'Устанавливаемый пароль с' 'овпадает с текущем.'
CURRENT_PASSWORD_IS_WRONG = 'Неверно указан текущий пароль.'
NOT_FOLLOW_SELF = 'Подписаться на самого себя нельзя.'
BASE64_IMAGE_ERROR = (
    'Ошибка передаваемого значения. Строка должна соответствовать BASE64.'
)
INGREDIENTS_REQUIRED = 'В рецепте не указан ни один ингредиент.'
TAGS_REQUIRED = 'В рецепте не указан ни один тег.'
RECIPE_INGREDIENTS_DUPLICATED = (
    'В рецепте не могут быть указаны повторяющиеся ингредиенты.'
)
RECIPE_TAGS_DUPLICATED = 'В рецепте не могут быть указаны повторяющиеся теги.'
RECIPE_UPDATE_REQUIRED_FIELDS = 'Не указаны обязательные поля'
INGREDIENT_DO_NOT_EXIST = 'Ингредиент с указанным id не найден.'

# Patterns
RECIPES_LIMIT_PARAM_PATTERN = r'[1-9]+\d*'
BASE64_IMAGE_PATTERN = (
    r'^data:image/(png|jpeg|jpg|gif|bmp|webp);base64,([A-Za-z0-9+/=\n\r]+)$'
)

# Auxiliary texts
INGREDIENTS_FILE_HEADER = 'Список ингредиентов к покупке'

# PDF generation consts
LEFT_MARGIN = 100
TOP_MARGIN = 50
BOTTOM = 50
LEADING = 25
MARGIN_AFTER_HEADER = 30

# Fields
RECIPE_REQUIRED_UPDATE_FIELD = [
    'ingredients',
    'tags',
    'name',
    'text',
    'cooking_time',
]
