import pytest
import random
import shutil
from django.conf import settings
from recipes.models import Ingredient, Recipe, ShoppingCart, Subscription
from users.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory


@pytest.fixture(autouse=True)
def cleanup_media(tmp_path):
    # Временный MEDIA_ROOT для тестов
    settings.MEDIA_ROOT = tmp_path / "media_test"
    yield
    # Удаляем папку после всех тестов
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)


@pytest.fixture
def sample_user():
    return User.objects.create_user(
        username="testchef",
        email="chef@example.com",
        password="testpass123"
    )

@pytest.fixture
def sample_ingredients():
    return [
        Ingredient.objects.create(name="Мука", measurement_unit="г"),
        Ingredient.objects.create(name="Сахар", measurement_unit="г")
    ]

@pytest.fixture
def sample_image():
    return SimpleUploadedFile(
        "test_image.jpg",
        b"file_content",
        content_type="image/jpeg"
    )


@pytest.fixture
def sample_recipe(sample_user_api, sample_image):
    """Фикстура для тестового рецепта."""
    return Recipe.objects.create(
        author=sample_user_api,
        name="Борщ",
        image=sample_image,
        text="Описание рецепта",
        cooking_time=30
    )

@pytest.fixture
def sample_recipe_alt(db, sample_another_user_api, sample_image):
    """Рецепт от другого автора."""
    return Recipe.objects.create(
        name='Суп',
        text='Простой суп',
        image=sample_image,
        cooking_time=30,
        author=sample_another_user_api
    )

@pytest.fixture
def sample_cart_item(sample_user, sample_recipe):
    """Фикстура для тестового элемента списка покупок."""
    return ShoppingCart.objects.create(
        user=sample_user,
        recipe=sample_recipe
    )


@pytest.fixture
def sample_author():
    """Фикстура для тестовой подписки."""
    return User.objects.create_user(
        username="test_author",
        email="author@example.com",
        password="testpass123"
    )


@pytest.fixture
def sample_user_api():
    return User.objects.create_user(
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        password="testpass123"
    )

@pytest.fixture
def sample_another_user_api():
    return User.objects.create_user(
        email="ggg@example.com",
        username="ggg",
        first_name="ggg",
        last_name="ggg",
        password="testpass123"
    )




@pytest.fixture
def sample_user_api_2():
    return User.objects.create_user(
        email="qwe@example.com",
        username="qwe",
        first_name="qwe",
        last_name="qwe",
        password="testpass123"
    )

@pytest.fixture
def sample_another_user_api_2():
    return User.objects.create_user(
        email="rty@example.com",
        username="rty",
        first_name="rty",
        last_name="rty",
        password="testpass123"
    )

@pytest.fixture
def another_user():
    from django.contrib.auth import get_user_model
    return get_user_model().objects.create_user(
        email="another@example.com",
        username="anotheruser",
        password="testpass"
    )

@pytest.fixture
def sample_user_data():
    return {
        "email": "new@example.com",
        "username": "newuser",
        "first_name": "New",
        "last_name": "User",
        "password": "newpass123"
    }


@pytest.fixture
def user_factory(db):
    def create_user(**kwargs):
        defaults = {
            'email': f"user{random.randint(1, 10000)}@example.com",
            'username': f"user{random.randint(1, 10000)}",
            'password': 'testpass123'
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)
    
    def create_batch(size, **kwargs):
        return [create_user(**kwargs) for _ in range(size)]
    
    return type('UserFactory', (), 
                {'create': create_user, 'create_batch': create_batch})

@pytest.fixture
def api_request():
    factory = APIRequestFactory()
    return factory.get('/')


@pytest.fixture
def sample_image():
    return SimpleUploadedFile(
        "avatar.jpg",
        b"file_content",
        content_type="image/jpeg"
    )


@pytest.fixture
def sample_image2():
    return SimpleUploadedFile(
        "new_avatar.png",
        b"new_content",
        content_type="image/png"
    )

@pytest.fixture
def base64_image():
    return (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAADUlEQVR42mP8z8BQDwAEhQGA"
        "hKmMIQAAAABJRU5ErkJggg=="
    )

@pytest.fixture
def base64_image_2():
    return (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAADUlEQVR42mP8z8BQDwAEhQGA"
        "hKmMIQAAAABJRU5ErkJggg=="
    )


@pytest.fixture
def sample_ingredient():
    from recipes.models import Ingredient
    return Ingredient.objects.create(
        name="Тестовый ингредиент",
        measurement_unit="г"
    )


@pytest.fixture
def another_ingredient():
    from recipes.models import Ingredient
    return Ingredient.objects.create(
        name="Другой ингредиент",
        measurement_unit="кг"
    )


@pytest.fixture
def sample_ingredients(db):
    """Фикстура тестовых ингредиентов."""
    return [
        Ingredient.objects.create(name='Мука', measurement_unit='г'),
        Ingredient.objects.create(name='Сахар', measurement_unit='г'),
        Ingredient.objects.create(name='Яйцо', measurement_unit='шт'),
    ]

@pytest.fixture
def existing_subscription(sample_user_api, sample_another_user_api):
    """Созданная подписка."""
    return Subscription.objects.create(user=sample_user_api, 
                                       author=sample_another_user_api)