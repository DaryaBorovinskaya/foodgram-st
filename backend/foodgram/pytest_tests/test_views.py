import pytest
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from recipes.models import Recipe, Favorite, ShoppingCart, Subscription

User = get_user_model()


@pytest.mark.django_db
class TestUserViewSet:
    """Тесты для UserViewSet."""

    def test_create_user(self, sample_user_data):
        """Тест создания пользователя."""
        client = APIClient()
        response = client.post('/api/users/', data=sample_user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='newuser').exists()

    def test_list_users(self):
        """Тест получения списка пользователей."""
        client = APIClient()
        response = client.get('/api/users/')
        
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_user(self, sample_user_api):
        """Тест получения конкретного пользователя."""
        client = APIClient()
        response = client.get(f'/api/users/{sample_user_api.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'

    def test_me_endpoint_authenticated(self, sample_user_api):
        """Тест endpoint /me для аутентифицированного пользователя."""
        client = APIClient()
        client.force_authenticate(user=sample_user_api)
        response = client.get('/api/users/me/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'

    def test_me_endpoint_unauthenticated(self):
        """Тест endpoint /me для неаутентифицированного пользователя."""
        client = APIClient()
        response = client.get('/api/users/me/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_pagination(self, user_factory):
        """Тест пагинации списка пользователей."""
        # Создаем 15 пользователей (вместе с sample_user_api будет 16)
        user_factory.create_batch(15)
        
        client = APIClient()
        response = client.get('/api/users/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'results' in response.data
        assert len(response.data['results']) == 6  


@pytest.mark.django_db
class TestIngredientViewSet:
    """Тесты для IngredientViewSet."""

    def test_list_ingredients(self):
        """Тест получения списка ингредиентов."""
        client = APIClient()
        response = client.get('/api/ingredients/')
        
        assert response.status_code == status.HTTP_200_OK

    def test_filter_ingredients_by_name(self, sample_ingredients):
        """Тест фильтрации ингредиентов по имени."""
        client = APIClient()
        response = client.get('/api/ingredients/', {'name': 'Сахар'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Сахар'

    def test_retrieve_ingredient(self, sample_ingredients):
        """Тест получения конкретного ингредиента."""
        client = APIClient()
        ingredient = sample_ingredients[0]
        response = client.get(f'/api/ingredients/{ingredient.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Мука'
        assert response.data['measurement_unit'] == 'г'

    def test_ingredient_permissions(self, sample_ingredients):
        """Тест разрешений (AllowAny)."""
        client = APIClient()
        response = client.get('/api/ingredients/')
        assert response.status_code == status.HTTP_200_OK

        # Проверка без аутентификации
        response = client.get('/api/ingredients/')
        assert response.status_code == status.HTTP_200_OK

   
@pytest.mark.django_db
class TestRecipeViewSet:
    """Тесты для RecipeViewSet."""

    def test_list_recipes(self, sample_recipe, sample_recipe_alt):
        """Тест получения списка рецептов."""
        client = APIClient()
        response = client.get('/api/recipes/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2

    def test_search_by_name(self, sample_recipe, sample_recipe_alt):
        """Тест поиска рецепта по имени."""
        client = APIClient()
        response = client.get('/api/recipes/?search=Борщ')
        assert response.status_code == status.HTTP_200_OK
        assert any("Борщ" in r["name"] for r in response.data["results"])

    def test_filter_by_author(self,
                              sample_another_user_api, sample_recipe_alt):
        """Тест фильтрации рецептов по автору."""
        client = APIClient()
        response = client.get(
            f'/api/recipes/?author={sample_another_user_api.id}')
        assert response.status_code == status.HTTP_200_OK
        assert all(r["author"]["username"] == "ggg" 
                   for r in response.data["results"])

    def test_add_to_favorite(self, sample_user_api, sample_recipe_alt):
        """Тест добавления рецепта в избранное."""
        client = APIClient()
        client.force_authenticate(user=sample_user_api)

        response = client.post(
            f'/api/recipes/{sample_recipe_alt.id}/favorite/')
        assert response.status_code == status.HTTP_201_CREATED
        assert Favorite.objects.filter(user=sample_user_api, 
                                       recipe=sample_recipe_alt).exists()

    def test_remove_from_favorite(self, sample_user_api, sample_recipe_alt):
        """Тест удаления рецепта из избранного."""
        Favorite.objects.create(user=sample_user_api, recipe=sample_recipe_alt)

        client = APIClient()
        client.force_authenticate(user=sample_user_api)
        response = client.delete(
            f'/api/recipes/{sample_recipe_alt.id}/favorite/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Favorite.objects.filter(user=sample_user_api, 
                                           recipe=sample_recipe_alt).exists()

    def test_add_to_shopping_cart(self, sample_user_api, sample_recipe_alt):
        """Тест добавления рецепта в список покупок."""
        client = APIClient()
        client.force_authenticate(user=sample_user_api)

        response = client.post(
            f'/api/recipes/{sample_recipe_alt.id}/shopping_cart/')
        assert response.status_code == status.HTTP_201_CREATED
        assert ShoppingCart.objects.filter(user=sample_user_api, 
                                           recipe=sample_recipe_alt).exists()

    def test_remove_from_shopping_cart(self, sample_user_api, 
                                       sample_recipe_alt):
        """Тест удаления рецепта из списка покупок."""
        ShoppingCart.objects.create(user=sample_user_api, 
                                    recipe=sample_recipe_alt)

        client = APIClient()
        client.force_authenticate(user=sample_user_api)

        response = client.delete(
            f'/api/recipes/{sample_recipe_alt.id}/shopping_cart/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ShoppingCart.objects.filter(
            user=sample_user_api, 
            recipe=sample_recipe_alt).exists()

    def test_download_shopping_cart(self, sample_user_api):
        """Тест загрузки списка покупок."""
        client = APIClient()
        client.force_authenticate(user=sample_user_api)

        response = client.get('/api/recipes/download_shopping_cart/')
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/pdf'

    def test_get_short_link(self, sample_recipe):
        """Тест получения короткой ссылки."""
        client = APIClient()
        response = client.get(f'/api/recipes/{sample_recipe.id}/get_link/')
        assert response.status_code == status.HTTP_200_OK
        assert 'short-link' in response.data


@pytest.mark.django_db
class TestSubscriptionViewSet:
    """Тесты для подписок."""

    def test_subscribe_success(self, sample_user_api, sample_another_user_api):
        """Тест успешной подписки."""
        client = APIClient()
        client.force_authenticate(user=sample_user_api)

        response = client.post(
            f'/api/users/{sample_another_user_api.id}/subscribe/')
        assert response.status_code == status.HTTP_201_CREATED
        assert Subscription.objects.filter(
            user=sample_user_api, 
            author=sample_another_user_api).exists()

    def test_subscribe_to_self(self, sample_user_api):
        """Тест подписки на самого себя."""
        client = APIClient()
        client.force_authenticate(user=sample_user_api)

        response = client.post(f'/api/users/{sample_user_api.id}/subscribe/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unsubscribe_success(self, sample_user_api, 
                                 sample_another_user_api, 
                                 existing_subscription):
        """Тест успешной отписки."""
        client = APIClient()
        client.force_authenticate(user=sample_user_api)

        response = client.delete(
            f'/api/users/{sample_another_user_api.id}/subscribe/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Subscription.objects.filter(
            user=sample_user_api, 
            author=sample_another_user_api).exists()

    def test_get_subscriptions(self, sample_user_api, existing_subscription):
        """Тест получения подписок."""
        client = APIClient()
        client.force_authenticate(user=sample_user_api)

        response = client.get('/api/users/subscriptions/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 1