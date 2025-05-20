import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import User
from recipes.models import (Ingredient, 
                            Recipe, Favorite, RecipeIngredient,
                            Subscription, ShoppingCart)


@pytest.mark.django_db
class TestUser:
    """Тесты для модели User."""

    def test_create_user_with_required_fields(self):
        """Тест создания пользователя с обязательными полями."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            password="testpass123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert not user.avatar

    def test_email_unique_constraint(self):
        """Тест уникальности email."""
        User.objects.create_user(
            username="user1",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            password="testpass123"
        )
        with pytest.raises(Exception):  
            User.objects.create_user(
                username="user2",
                email="test@example.com",
                first_name="Jane",
                last_name="Smith",
                password="testpass123"
            )

    def test_user_required_fields_validation(self):
        """Тест обязательности first_name и last_name."""
        with pytest.raises(ValidationError):
            user = User(
                username="testuser",
                email="test@example.com",
                password="testpass123"
            )
            user.full_clean()

    def test_avatar_upload(self):
        """Тест загрузки аватара."""
        fake_image = SimpleUploadedFile(
            "avatar.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            password="testpass123",
            avatar=fake_image
        )
        assert "users/avatar.jpg" in user.avatar.url


@pytest.mark.django_db
class TestIngredient:
    """Тесты для модели Ingredient."""

    def test_create_ingredient(self):
        """Тест создания ингредиента с обязательными полями."""
        ingredient = Ingredient.objects.create(
            name="Мука",
            measurement_unit="г"
        )
        assert ingredient.name == "Мука"
        assert ingredient.measurement_unit == "г"
        assert str(ingredient) == "Мука (г)"

    def test_ingredient_unique_constraint(self):
        """Тест уникальности комбинации name + measurement_unit."""
        Ingredient.objects.create(name="Сахар", measurement_unit="г")
        
        with pytest.raises(Exception):  # Должно вызвать IntegrityError
            Ingredient.objects.create(name="Сахар", measurement_unit="г")

    def test_ingredient_required_fields_validation(self):
        """Тест обязательности полей name и measurement_unit."""
        with pytest.raises(ValidationError):
            ingredient = Ingredient()  # Пустые обязательные поля
            ingredient.full_clean()


@pytest.mark.django_db
class TestRecipe:
    """Тесты для модели Recipe."""

    def test_recipe_creation(self, sample_user, 
                             sample_ingredients, sample_image):
        """Тест создания рецепта с ингредиентами и количеством."""
        recipe = Recipe.objects.create(
            author=sample_user,
            name="Тестовый рецепт",
            image=sample_image,
            text="Описание рецепта",
            cooking_time=30
        )
        
        # Добавляем ингредиенты с указанием количества
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=sample_ingredients[0],
            amount=200 
        )
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=sample_ingredients[1],
            amount=100
        )
        
        assert recipe.ingredients.count() == 2
        assert recipe.recipe_ingredients.first().amount == 200

    def test_recipe_required_fields(self, sample_user):
        """Тест обязательных полей модели."""
        with pytest.raises(ValidationError):
            recipe = Recipe(
                author=sample_user,
                # Пропущены name, image, text, cooking_time
            )
            recipe.full_clean()

    def test_favorites_count_property(self, sample_user, sample_image):
        """Тест свойства favorites_count."""
        # Создаем тестовый рецепт
        recipe = Recipe.objects.create(
            author=sample_user,
            name="Избранный рецепт",
            image=sample_image,
            text="Рецепт для теста избранного",
            cooking_time=15
        )
        
        Favorite.objects.create(user=sample_user, recipe=recipe)
        another_user = User.objects.create_user(
            username="user2", email="user2@example.com")
        Favorite.objects.create(user=another_user, recipe=recipe)
        
        assert recipe.favorites_count == 2


@pytest.mark.django_db
class TestFavorite:
    """Тесты для модели Favorite."""

    def test_favorite_creation(self, sample_user, sample_recipe):
        """Тест создания записи в избранном."""
        favorite = Favorite.objects.create(
            user=sample_user,
            recipe=sample_recipe
        )
        
        assert favorite.user == sample_user
        assert favorite.recipe == sample_recipe
        assert str(favorite) == f"{sample_user} -> {sample_recipe}"

    def test_favorite_unique_constraint(self, sample_user, sample_recipe):
        """Тест уникальности пары пользователь-рецепт."""
        Favorite.objects.create(user=sample_user, recipe=sample_recipe)
        
        with pytest.raises(Exception):  # Должно вызвать IntegrityError
            Favorite.objects.create(user=sample_user, recipe=sample_recipe)

    def test_favorite_required_fields(self):
        """Тест обязательных полей модели."""
        with pytest.raises(ValidationError):
            favorite = Favorite()  # Пустые обязательные поля
            favorite.full_clean()


@pytest.mark.django_db
class TestShoppingCart:
    """Тесты для модели ShoppingCart."""

    def test_shopping_cart_creation(self, sample_cart_item, sample_user, 
                                    sample_recipe):
        """Тест создания записи в списке покупок."""
        assert sample_cart_item.user == sample_user
        assert sample_cart_item.recipe == sample_recipe
        assert str(sample_cart_item) == f"{sample_user} -> {sample_recipe}"

    def test_shopping_cart_required_fields(self):
        """Тест обязательных полей модели."""
        with pytest.raises(ValidationError):
            cart_item = ShoppingCart()  # Пустые обязательные поля
            cart_item.full_clean()

    def test_user_shopping_cart_relation(self, sample_cart_item, sample_user):
        """Тест связи пользователя с корзиной."""
        assert sample_user.shopping_cart.count() == 1
        assert sample_user.shopping_cart.first() == sample_cart_item

    def test_recipe_shopping_cart_relation(self, sample_cart_item, 
                                           sample_recipe):
        """Тест связи рецепта с корзиной."""
        assert sample_recipe.shopping_cart.count() == 1
        assert sample_recipe.shopping_cart.first() == sample_cart_item


@pytest.mark.django_db
class TestSubscription:
    """Тесты для модели Subscription."""

    def test_subscription_creation(self, sample_user, sample_author):
        """Тест создания подписки."""
        subscription = Subscription.objects.create(
            user=sample_user,
            author=sample_author
        )
        
        assert subscription.user == sample_user
        assert subscription.author == sample_author

    def test_subscription_unique_constraint(self, sample_user, sample_author):
        """Тест уникальности пары подписчик-автор."""
        Subscription.objects.create(user=sample_user, author=sample_author)
        
        with pytest.raises(Exception):
            Subscription.objects.create(user=sample_user, author=sample_author)

    def test_subscription_required_fields(self):
        """Тест обязательных полей модели."""
        with pytest.raises(ValidationError):
            sub = Subscription()  # Пустые обязательные поля
            sub.full_clean()

    def test_user_followers_relation(self, sample_user, sample_author):
        """Тест связей подписчиков."""
        Subscription.objects.create(user=sample_user, author=sample_author)
        
        assert sample_author.following.count() == 1
        assert sample_user.follower.count() == 1
