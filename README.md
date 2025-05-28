# FOODGRAM
Проект сайта, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов.

## Как запустить

1. Клонирование репозитория
```
git clone https://github.com/DaryaBorovinskaya/foodgram-st.git
```

2. Находясь в корневой директории проекта (foodgram-st), выполните команду:
```
docker compose up
```

3. После запусков контейнеров выполните миграции и загрузите ингредиенты(находясь в той же директории):
```
docker compose exec backend python manage.py migrate
```

```
docker compose exec backend python manage.py loaddata ingredients_fixed.json
```
4. После выполненных миграций сайт станет доступен по адресу http://localhost:8001/