from rest_framework import serializers, status
from django.contrib.auth import get_user_model
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription, Favorite, MAX_VALUE_POSITIVE_SMALL_INT, 
    MIN_VALUE_POSITIVE_SMALL_INT 
)
from django.contrib.auth.hashers import make_password
from drf_extra_fields.fields import Base64ImageField

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
            "avatar",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "username": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    # Оформление вывода как в API-документации
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        if request and request.method == "POST":
            representation.pop("is_subscribed", None)
            representation.pop("avatar", None)
        return representation

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
            "is_subscribed",
            "avatar",
        )
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "email": {"required": False},
            "username": {"required": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def update(self, instance, validated_data):
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
            del validated_data["password"]
        return super().update(instance, validated_data)

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.follower.filter(author=obj).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar and hasattr(obj.avatar, "url"):
            return obj.avatar.url
        return None


class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)

    def update(self, instance, validated_data):
        avatar_file = validated_data.get("avatar")

        if avatar_file:
            if instance.avatar:
                instance.avatar.delete(save=False)
            filename = avatar_file.name if hasattr(
                avatar_file, 'name') else 'avatar.png'
            instance.avatar.save(filename, avatar_file, save=True)

        return instance


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, write_only=True)
    current_password = serializers.CharField(required=True, write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверен")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    name = serializers.StringRelatedField(
        source="ingredient.name", read_only=True)
    measurement_unit = serializers.StringRelatedField(
        source="ingredient.measurement_unit", read_only=True
    )
    amount = serializers.IntegerField( 
        min_value=MIN_VALUE_POSITIVE_SMALL_INT,
        max_value=MAX_VALUE_POSITIVE_SMALL_INT
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.follower.filter(author=obj).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar and hasattr(obj.avatar, "url"):
            return obj.avatar.url
        return None


class RecipeSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source="recipe_ingredients")
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField( 
        min_value=MIN_VALUE_POSITIVE_SMALL_INT,
        max_value=MAX_VALUE_POSITIVE_SMALL_INT
    )


    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "image",
            "name",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                "Поле image не может быть пустым.")
        return value

    def validate(self, data):
        ingredients = data.get("recipe_ingredients")
        if not ingredients:
            raise serializers.ValidationError(
                {"ingredients": "Нужно добавить хотя бы один ингредиент."}
            )

        ingredient_ids = [item["ingredient"].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты не должны повторяться."}
            )
        return data

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.shopping_cart.filter(user=request.user).exists()
        return False

    def _save_ingredients(self, recipe, ingredients):
        objs = []
        for item in ingredients:
            ingredient = item["ingredient"]
            amount = item["amount"]
            objs.append(
                RecipeIngredient(
                    recipe=recipe, 
                    ingredient=ingredient, 
                    amount=amount
                )
            )
        RecipeIngredient.objects.bulk_create(objs)

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients")
        recipe = Recipe(**validated_data)
        recipe.full_clean()
        recipe.save()
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.full_clean()
        instance.save()

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._save_ingredients(instance, ingredients_data)

        return instance


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ("user", "recipe")


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source="author.avatar", read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def validate(self, data):
        author = self.context.get('author')
        if self.context['request'].user == author:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя",
                code=status.HTTP_400_BAD_REQUEST
            )
        return data


    def get_is_subscribed(self, obj):
        # Проверка, подписан ли текущий пользователь на автора
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.author.following.filter(user=request.user).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        queryset = obj.author.recipes.all()
        if limit:
            queryset = queryset[: int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()
