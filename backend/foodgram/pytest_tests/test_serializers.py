import pytest
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from api.serializers import (UserSerializer, AvatarSerializer,
                             SetPasswordSerializer,
                             IngredientSerializer,
                             AuthorSerializer,
                             RecipeSerializer, 
                             SubscriptionSerializer)
from recipes.models import Subscription, Favorite, ShoppingCart, Recipe
from users.models import User
from rest_framework.test import APIRequestFactory, force_authenticate
import os
import base64
from django.core.files.base import ContentFile
from django.contrib.auth.models import AnonymousUser


class TestUserSerializer:
    """Тесты для UserSerializer."""
    
    @pytest.mark.django_db
    def test_serialization(self, sample_user_api, api_request):
        """Тест сериализации пользователя."""
        api_request.user = sample_user_api
        serializer = UserSerializer(
            instance=sample_user_api,
            context={'request': api_request}
        )
        data = serializer.data
        
        assert data['email'] == "test@example.com"
        assert data['username'] == "testuser"
        assert data['first_name'] == "Test"
        assert data['last_name'] == "User"
        assert 'password' not in data  # Пароль write_only
        assert data['is_subscribed'] is False
        assert 'avatar' in data

    @pytest.mark.django_db
    def test_create_user(self):
        """Тест создания пользователя."""
        data = {
            "email": "new@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "newpass123"
        }
        serializer = UserSerializer(data=data)
        assert serializer.is_valid()
        user = serializer.save()
        
        assert user.email == "new@example.com"
        assert user.check_password("newpass123")
        assert user.username == "newuser"

    @pytest.mark.django_db
    def test_create_user_missing_fields(self):
        """Тест валидации при отсутствии обязательных полей."""
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.post('/')
        
        data = {
            "email": "new@example.com",
            # Пропущены username, first_name, last_name, password
        }
        serializer = UserSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()

        errors = serializer.errors
        assert 'username' in errors
        assert 'first_name' in errors
        assert 'last_name' in errors
        assert 'password' in errors

    @pytest.mark.django_db
    def test_update_user(self, sample_user_api):
        """Тест обновления пользователя."""
        data = {
            "first_name": "Updated",
            "password": "newpassword123"
        }
        serializer = UserSerializer(
            instance=sample_user_api,
            data=data,
            partial=True
        )
        assert serializer.is_valid()
        user = serializer.save()
        
        assert user.first_name == "Updated"
        assert user.check_password("newpassword123")

    @pytest.mark.django_db
    def test_is_subscribed_field(self, sample_user_api):
        """Тест поля is_subscribed."""
        user1 = User.objects.create_user(
            email="user1@example.com",
            username="user1",
            password="testpass"
        )
        user2 = User.objects.create_user(
            email="user2@example.com",
            username="user2",
            password="testpass"
        )
        
        # Создаем подписку
        Subscription.objects.create(user=user1, author=user2)
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user1
        
        serializer = UserSerializer(
            instance=user2,
            context={'request': request}
        )
        
        assert serializer.data['is_subscribed'] is True

    @pytest.mark.django_db
    def test_avatar_serialization(self, sample_user_api, sample_image):
        """Тест сериализации аватара."""
        sample_user_api.avatar = sample_image
        sample_user_api.save()
        
        serializer = UserSerializer(instance=sample_user_api)
        assert 'avatar' in serializer.data
        assert 'avatar.jpg' in serializer.data['avatar']

    @pytest.mark.django_db
    def test_post_request_fields(self):
        """Тест обязательных полей при POST-запросе."""
        factory = APIRequestFactory()
        request = factory.post('/')
        
        serializer = UserSerializer(context={'request': request})
        
        assert serializer.fields['email'].required is True
        assert serializer.fields['username'].required is True
        assert serializer.fields['first_name'].required is True
        assert serializer.fields['last_name'].required is True
        assert serializer.fields['password'].required is True

    @pytest.mark.django_db
    def test_non_post_request_fields(self):
        """Тест необязательных полей при не-POST запросах."""
        factory = APIRequestFactory()
        request = factory.get('/')
        
        serializer = UserSerializer(context={'request': request})
        
        assert serializer.fields['email'].required is False
        assert serializer.fields['username'].required is False
        assert serializer.fields['first_name'].required is False
        assert serializer.fields['last_name'].required is False
        assert serializer.fields['password'].required is False

    @pytest.mark.django_db
    def test_to_representation_post(self, sample_user_api):
        """Тест преобразования при POST-запросе."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = sample_user_api  
        
        serializer = UserSerializer(
            instance=sample_user_api,
            context={'request': request}
        )
        data = serializer.data
        
        assert 'is_subscribed' not in data
        assert 'avatar' not in data


class TestAvatarSerializer:
    """Тесты для AvatarSerializer."""
    
    @pytest.mark.django_db
    def test_serialization(self, sample_user_api, sample_image):
        """Тест сериализации аватара."""
        sample_user_api.avatar = sample_image
        sample_user_api.save()
        
        serializer = AvatarSerializer(instance=sample_user_api)
        data = serializer.data
        
        assert 'avatar' in data
        assert data['avatar'].startswith('/media/users/avatar')
        assert data['avatar'].endswith('.jpg')

    @pytest.mark.django_db
    def test_validation(self, base64_image):
        """Тест валидации с корректными данными в base64."""
        
        data = {"avatar": base64_image}
        serializer = AvatarSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    @pytest.mark.django_db
    def test_validation_missing_field(self):
        """Тест валидации при отсутствии обязательного поля."""
        serializer = AvatarSerializer(data={})
        
        assert not serializer.is_valid()
        assert 'avatar' in serializer.errors
        assert serializer.errors['avatar'][0].code == 'required'

    @pytest.mark.django_db
    def test_update_avatar(self, sample_user_api, base64_image, base64_image_2):
        
        format1, imgstr1 = base64_image.split(';base64,')
        data1 = base64.b64decode(imgstr1)
        sample_user_api.avatar.save("avatar1.png", 
                                    ContentFile(data1), save=True)
        old_avatar_path = sample_user_api.avatar.path
        old_avatar_name = os.path.basename(old_avatar_path)
        data = {"avatar": base64_image_2}
        serializer = AvatarSerializer(instance=sample_user_api, data=data)
        assert serializer.is_valid(), serializer.errors
        updated_user = serializer.save()
        new_avatar_name = os.path.basename(updated_user.avatar.name)
        assert new_avatar_name != old_avatar_name


        
    @pytest.mark.django_db
    def test_update_with_invalid_data(self, sample_user_api):
        """Тест обновления с невалидными данными."""
        serializer = AvatarSerializer(
            instance=sample_user_api,
            data={"avatar": "not_an_image"} 
        )
        
        assert not serializer.is_valid()
        assert 'avatar' in serializer.errors

    @pytest.mark.django_db
    def test_required_field(self):
        """Тест обязательности поля avatar."""
        serializer = AvatarSerializer()
        assert serializer.fields['avatar'].required is True


class TestSetPasswordSerializer:
    """Тесты для SetPasswordSerializer."""
    
    @pytest.mark.django_db
    def test_validation_fail_wrong_current_password(self, sample_user_api):
        """Тест валидации при неверном текущем пароле."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = sample_user_api
        
        data = {
            "new_password": "new_secure_password123",
            "current_password": "wrong_password"
        }
        
        serializer = SetPasswordSerializer(
            data=data,
            context={'request': request}
        )
        
        assert not serializer.is_valid()
        assert 'current_password' in serializer.errors
        assert "Текущий пароль неверен" in str(serializer.errors['current_password'])
    
    @pytest.mark.django_db
    def test_save_success(self, sample_user_api):
        """Тест успешного изменения пароля."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = sample_user_api
        
        old_password_hash = sample_user_api.password
        new_password = "new_secure_password123"
        
        data = {
            "new_password": new_password,
            "current_password": "testpass123" 
        }
        
        serializer = SetPasswordSerializer(
            data=data,
            context={'request': request}
        )
        
        assert serializer.is_valid()
        serializer.save()
        
        # Проверяем, что пароль действительно изменился
        sample_user_api.refresh_from_db()
        assert sample_user_api.check_password(new_password)
        assert sample_user_api.password != old_password_hash
    

class TestIngredientSerializer:
    """Тесты для IngredientSerializer."""

    @pytest.mark.django_db
    def test_create_ingredient(self):
        """Тест создания ингредиента."""
        data = {
            "name": "Новый ингредиент",
            "measurement_unit": "г"
        }
        serializer = IngredientSerializer(data=data)
        assert serializer.is_valid()
        ingredient = serializer.save()
        
        assert ingredient.name == "Новый ингредиент"
        assert ingredient.measurement_unit == "г"
        assert ingredient.id is not None

    @pytest.mark.django_db
    def test_create_ingredient_missing_fields(self):
        """Тест валидации при отсутствии обязательных полей."""
        # Тест без name
        data1 = {"measurement_unit": "г"}
        serializer1 = IngredientSerializer(data=data1)
        assert not serializer1.is_valid()
        assert 'name' in serializer1.errors
        
        # Тест без measurement_unit
        data2 = {"name": "Без единицы измерения"}
        serializer2 = IngredientSerializer(data=data2)
        assert not serializer2.is_valid()
        assert 'measurement_unit' in serializer2.errors

    
class TestAuthorSerializer:
    """Тесты для AuthorSerializer."""
    
    @pytest.mark.django_db
    def test_serialization(self, sample_user_api, base64_image):
        """Тест базовой сериализации автора."""
        format, imgstr = base64_image.split(';base64,') 
        ext = format.split('/')[-1]  
        decoded_img = base64.b64decode(imgstr)
        sample_user_api.avatar.save(
            f"avatar_{sample_user_api.id}.{ext}",
            ContentFile(decoded_img),
            save=True
        )
        sample_user_api.save()
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = sample_user_api
        
        serializer = AuthorSerializer(
            instance=sample_user_api,
            context={'request': request}
        )
        data = serializer.data
        
        assert set(data.keys()) == {
            "email", "id", "username", 
            "first_name", "last_name",
            "is_subscribed", "avatar"
        }
        assert data['email'] == sample_user_api.email
        assert data['username'] == sample_user_api.username
        assert data['is_subscribed'] is False
        assert 'avatar' in data

    @pytest.mark.django_db
    def test_is_subscribed_field_true(self, sample_user_api, another_user):
        """Тест поля is_subscribed (True случай)."""
        # Создаем подписку
        Subscription.objects.create(user=sample_user_api, author=another_user)
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = sample_user_api
        
        serializer = AuthorSerializer(
            instance=another_user,
            context={'request': request}
        )
        
        assert serializer.data['is_subscribed'] is True

    @pytest.mark.django_db
    def test_is_subscribed_field_false(self, sample_user_api, another_user):
        """Тест поля is_subscribed (False случай)."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = sample_user_api
        
        serializer = AuthorSerializer(
            instance=another_user,
            context={'request': request}
        )
        
        assert serializer.data['is_subscribed'] is False

    @pytest.mark.django_db
    def test_is_subscribed_anonymous(self, sample_user_api):
        """Тест is_subscribed для анонимного пользователя."""
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        
        serializer = AuthorSerializer(
            instance=sample_user_api,
            context={'request': request}
        )
        
        assert serializer.data['is_subscribed'] is False

    @pytest.mark.django_db
    def test_avatar_field_no_avatar(self, sample_user_api):
        """Тест поля avatar (когда аватара нет)."""
        serializer = AuthorSerializer(instance=sample_user_api)
        assert serializer.data['avatar'] is None

    
class TestRecipeSerializer:
    """Тесты для RecipeSerializer."""

    @pytest.mark.django_db
    def test_create_recipe(self, sample_user_api, 
                           sample_ingredient, base64_image):
        """Тест создания рецепта."""
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = sample_user_api
        
        image = base64_image
        data = {
            "name": "Новый рецепт",
            "text": "Описание рецепта",
            "cooking_time": 30,
            "image": image,
            "ingredients": [
                {
                    "id": sample_ingredient.id,
                    "amount": 100
                }
            ]
        }
        
        request = factory.post('/', data=data, format='multipart')
        request.user = sample_user_api
        
        serializer = RecipeSerializer(
            data=data,
            context={'request': request}
        )
        
        assert serializer.is_valid(), serializer.errors  
        recipe = serializer.save(author=sample_user_api)
        
        assert recipe.name == data['name']
        assert recipe.ingredients.count() == 1
        assert recipe.recipe_ingredients.first().amount == 100

    @pytest.mark.django_db
    def test_validate_ingredients(self, sample_ingredient):
        """Тест валидации ингредиентов."""
        serializer = RecipeSerializer()
        
        # Нет ингредиентов
        with pytest.raises(ValidationError):
            serializer.validate({"name": "Рецепт без ингредиентов"})
        
        # Дублирующиеся ингредиенты
        data = {
            "recipe_ingredients": [
                {"ingredient": sample_ingredient, "amount": 100},
                {"ingredient": sample_ingredient, "amount": 200}
            ]
        }
        with pytest.raises(ValidationError):
            serializer.validate(data)

    @pytest.mark.django_db
    def test_is_favorited_field(self, sample_recipe, sample_user_api):
        """Тест поля is_favorited."""
        factory = APIRequestFactory()
        
        # Не в избранном
        request1 = factory.get('/')
        request1.user = sample_user_api
        serializer1 = RecipeSerializer(
            instance=sample_recipe,
            context={'request': request1}
        )
        assert serializer1.data['is_favorited'] is False
        
        # В избранном
        Favorite.objects.create(user=sample_user_api, recipe=sample_recipe)
        request2 = factory.get('/')
        request2.user = sample_user_api
        serializer2 = RecipeSerializer(
            instance=sample_recipe,
            context={'request': request2}
        )
        assert serializer2.data['is_favorited'] is True

    @pytest.mark.django_db
    def test_is_in_shopping_cart_field(self, sample_recipe, sample_user_api):
        """Тест поля is_in_shopping_cart."""
        factory = APIRequestFactory()
        
        # Не в корзине
        request1 = factory.get('/')
        request1.user = sample_user_api
        serializer1 = RecipeSerializer(
            instance=sample_recipe,
            context={'request': request1}
        )
        assert serializer1.data['is_in_shopping_cart'] is False
        
        # В корзине
        ShoppingCart.objects.create(user=sample_user_api, recipe=sample_recipe)
        request2 = factory.get('/')
        request2.user = sample_user_api
        serializer2 = RecipeSerializer(
            instance=sample_recipe,
            context={'request': request2}
        )
        assert serializer2.data['is_in_shopping_cart'] is True

    @pytest.mark.django_db
    def test_update_recipe(self, sample_recipe, another_ingredient,
                           base64_image):
        """Тест обновления рецепта."""
        data = {
            "name": "Обновленное название",
            "ingredients": [
                {
                    "id": another_ingredient.id,
                    "amount": 200
                }
            ]
        }
        
        data = {
            "name": "Обновленное название",
            "text": "Обновленное описание",
            "cooking_time": 45,
            "image": base64_image,
            "ingredients": [
                {
                    "id": another_ingredient.id,
                    "amount": 200
                }
            ]
        }
    
        factory = APIRequestFactory()
        request = factory.put('/')
        request.user = sample_recipe.author
        
        serializer = RecipeSerializer(
            instance=sample_recipe,
            data=data,
            context={'request': request},
            partial=True
        )
        
        assert serializer.is_valid(), serializer.errors
        
        recipe = serializer.save()
        
        assert recipe.name == "Обновленное название"
        assert recipe.text == "Обновленное описание"
        assert recipe.cooking_time == 45
        assert recipe.ingredients.count() == 1
        assert recipe.ingredients.first() == another_ingredient
        assert recipe.recipe_ingredients.first().amount == 200


class TestSubscriptionSerializer:
    """Тесты для SubscriptionSerializer."""

    @pytest.mark.django_db  
    def test_get_is_subscribed_true(self, sample_user_api_2, 
                                    sample_another_user_api_2):
        """Тест is_subscribed=True когда пользователь подписан."""
        factory = APIRequestFactory()
        request = factory.get('/')
        force_authenticate(request, user=sample_user_api_2)
        # Создаем подписку
        Subscription.objects.create(
            user=sample_user_api_2,
            author=sample_another_user_api_2
        )

        subscription = Subscription.objects.get(
            author=sample_another_user_api_2)
        
        drf_request = Request(request)
        serializer = SubscriptionSerializer(
            subscription,
            context={'request': drf_request}
        )

        assert serializer.data['is_subscribed'] is True

    @pytest.mark.django_db  
    def test_get_recipes_count(self, sample_user_api_2, 
                               sample_recipe, sample_image):
        """Тест правильного подсчета количества рецептов."""
        factory = APIRequestFactory()
        request = factory.get('/')
        force_authenticate(request, user=sample_user_api_2)
        
        Recipe.objects.create(
            author=sample_recipe.author,
            name='Recipe 2',
            image=sample_image,
            text='Description 2',
            cooking_time=15
        )
        Recipe.objects.create(
            author=sample_recipe.author,
            name='Recipe 3',
            image=sample_image,
            text='Description 3',
            cooking_time=20
        )

        subscription = Subscription.objects.create(
            author=sample_recipe.author,
            user=sample_user_api_2
        )
        drf_request = Request(request)
        serializer = SubscriptionSerializer(
            subscription,
            context={'request': drf_request}
        )

        assert serializer.data['recipes_count'] == 3

