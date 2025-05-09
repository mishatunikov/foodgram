# Foodgram

Цель данного проекта - предоставлять пользователям возможность создавать и хранить рецепты на онлайн платформе, добавлять 
в избранное понравившиеся рецепты, создавать корзину покупок, на основе которой получать список необходимых ингредиентов 
для приготовления выбранных блюд.

Проект доступен по адресу: https://foodgrammer.zapto.org/

## Стэк технологии
### Backend:
- [Python3.9](https://www.python.org/)
- [Django3.2](https://www.djangoproject.com/)
- [Django Rest Framework](https://www.django-rest-framework.org/)
- [Djoser](https://djoser.readthedocs.io/en/latest/introduction.html)
- [PostgreSQL](https://www.postgresql.org/)
- [Gunicorn](https://gunicorn.org/)

### Frontend: 
- [React](https://react.dev/)

### Инфраструктура
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Nginx](https://nginx.org/ru/)
- [GitHub Actions](https://github.com/features/actions)
_______________________________________________________________________________

## Локальный запуск проекта с помощью Docker compose
1. Скопируйте репозиторий:
    ```
    git clone https://github.com/mishatunikov/foodgram.git
    ```

2. Создайте файл .env и наполните его необходимыми переменными окружения (следуйте примеру .env_example).
3. Для локального запуска используйте файл docker-compose.yml. Перейдите в корень проекта, где находится данный файл и выполните команду:
   ```
   docker compose up
   ```
4. Выполните миграции БД:
   ```
   docker compose exec backend python manage.py migrate
   ```
5. Соберите статику backend и скопируйте её в нужную директорию:
   ```
   docker compose exec backend python manage.py collectstatic
   ```
   ```
   docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
   ```
6. В директории fixtures находятся фикстуры для наполнения БД тестовыми данными:
   - ingredients_tags.json - фикстура для заполнения БД данными об ингредиентах и тегах
   - recipes.json - фикстура для заполнения БД данными о пользователях и рецептах (включает в себя информацию об ингредиентах и тегах)
   
   Чтобы применить фикстуру, выполните команду (пример применения фикстуры recipes.json):
   ```
   docker compose exec backend python manage.py loaddata fixtures/recipes.json
   ```
   
   Стоит отметить, что для корректного отображения пользовательских аватаров / изображений рецептов, нужно скопировать заранее подготовленные файлы изображений (fixtures/fixtures_media)
   в папку /media/ контейнера backend, для этого выполните команду:
   ```
   docker compose exec backend cp -r fixtures/fixtures_media/. media/.
   ```

7. Создайте суперпользователя для управления админкой:
   ```
   docker compose exec backend python manage.py createsuperuser
   ```

## CI/CD
Проект включает в себя workflow на базе Git Actions для автоматизации деплоя (CI/CD). Он включает в себя:
- Запуск линтеров и тестов
- Сборку новых образов и отправку их на DockerHub
- Обновление образов и перезапуск контейнеров удаленном сервере
- Уведомление в телеграм об успешном выполнении workflow

Для корректной работы Git Actions создайте следующие git values (для этого перейдите в раздел Actions secrets and variables):
- DOCKER_PASSWORD (пароль от DockerHub)
- DOCKER_USERNAME (Username от DockerHub)
- HOST (название хоста)
- SSH_KEY (для подключения к удаленному серверу)
- SSH_PASSPHRASE (passphrase для подключения к удаленному серверу)
- USER (имя пользователя удаленного сервера)
- TELEGRAM_TO (ID телеграм аккаунта для уведомления)
- TELEGRAM_TOKEN (токен бота в телеграм для отправки уведомления)


## Доступные эндпоинты API

Для просмотра подробной документации API используйте эндпоинт - `api/docs/`

### Пользователи:
- __GET /api/users/__ — Получить список пользователей (с пагинацией).
- __POST /api/users/__ — Зарегистрировать нового пользователя.
- __GET /api/users/{id}/__ — Получить профиль пользователя по ID.
- __GET /api/users/me/__ — Получить информацию о текущем авторизованном пользователе.
- __PUT /api/users/me/avatar/__ — Добавить аватар текущему пользователю.
- __DELETE /api/users/me/avatar/__ — Удалить аватар текущего пользователя.
- __GET /api/users/subscriptions/__ — Получить список пользователей, на которых подписан текущий пользователь.
- __POST /api/users/{id}/subscribe/__ — Подписаться на пользователя.
- __DELETE /api/users/{id}/subscribe/__ — Отписаться от пользователя.
- __POST /api/users/set_password/__ — Изменить пароль текущего пользователя.

### Теги:
- __GET /api/tags/__ — Получить список тегов.
- __GET /api/tags/{id}/__ — Получить информацию о конкретном теге.

### Рецепты:
- __GET /api/recipes/__ — Получить список рецептов (с фильтрами по автору, тегам, избранному и т.д.).
- __POST /api/recipes/__ — Создать новый рецепт (доступно только авторизованным пользователям).
- __GET /api/recipes/{id}/__ — Получить рецепт по ID.
- __PATCH /api/recipes/{id}/__ — Обновить рецепт по ID (доступно только автору рецепта).
- __DELETE /api/recipes/{id}/__ — Удалить рецепт по ID (доступно только автору рецепта).
- __GET /api/recipes/{id}/get-link/__ — Получить короткую ссылку на рецепт.
- __POST /api/recipes/{id}/favorite/__ — Добавить рецепт в избранное.
- __DELETE /api/recipes/{id}/favorite/__ — Удалить рецепт из избранного.
- __POST /api/recipes/{id}/shopping_cart/__ — Добавить рецепт в список покупок.
- __DELETE /api/recipes/{id}/shopping_cart/__ — Удалить рецепт из списка покупок.
- __GET /api/recipes/download_shopping_cart/__ — Скачать файл со списком покупок.

### Ингредиенты:
- __GET /api/ingredients/__ — Получить список ингредиентов (с возможностью поиска по имени).
- __GET /api/ingredients/{id}/__ — Получить информацию о конкретном ингредиенте.

### Авторизация:
- __POST /api/auth/token/login/__ — Получить токен для авторизации.
- __POST /api/auth/token/logout/__ — Удалить токен текущего пользователя (разлогиниться).