# FOODGRAM
Проект сайта, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов.

## При запуске тестов в Postman:
Значение Collection {{baseUrl}} поменять на http://127.0.0.1:8001

## Как запустить

1. Клонирование репозитория
```
git clone https://github.com/DaryaBorovinskaya/foodgram-st.git
```

2. Находясь в корневой директории проекта (foodgram-st), выполните команду:
```
docker compose up
```

3. После запусков контейнеров ОБЯЗАТЕЛЬНО выполните миграции и загрузите ингредиенты(находясь в той же директории):
```
docker compose exec backend python manage.py migrate
```

```
docker compose exec backend python manage.py loaddata ingredients_fixed.json
```
4. После выполненных миграций сайт станет доступен по адресу http://localhost:8001/