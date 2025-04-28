from rest_framework import serializers
from django.contrib.auth import get_user_model
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    Subscription
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                following=obj
            ).exists()
        return False


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)


class SetAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    name = serializers.StringRelatedField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        read_only_fields = ('author',)

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(**validated_data)
        
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )
        
        return recipe


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'user',
            'following',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        queryset = obj.following.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()
