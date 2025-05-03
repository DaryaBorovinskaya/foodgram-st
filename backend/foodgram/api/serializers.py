from rest_framework import serializers
from django.contrib.auth import get_user_model
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    Subscription,
)
import json
# from djoser.serializers import UserSerializer as BaseUserSerializer
# from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from django.contrib.auth.hashers import make_password
import base64
import imghdr
import os
from django.core.files.base import ContentFile


User = get_user_model()


# class CustomUserSerializer(BaseUserSerializer):

#     class Meta:
#         model = User
#         fields = ('email', 'id', 'username',
#                   'first_name', 'last_name',)
#         read_only_fields = ('id',)

#     # Оформление вывода как в API-документации
#     def to_representation(self, instance):
#         representation = super().to_representation(instance)
#         representation.pop('is_subscribed')
#         representation.pop('avatar')
#         return representation


# class UserCreateSerializer(BaseUserCreateSerializer):
#     class Meta(BaseUserCreateSerializer.Meta):
#         fields = ('email', 'username', 'first_name', 'last_name', 'password')


class Base64Image:
    def handle_base64_image(self, field_name, data):
        if (
            field_name in data
            and isinstance(data[field_name], str)
            and data[field_name].startswith("data:image")
        ):
            format, imgstr = data[field_name].split(";base64,")
            ext = format.split("/")[-1]
            filename = f'{field_name}_{self.context.get("request").user.id if self.context.get("request") else "temp"}.{ext}'
            data[field_name] = ContentFile(base64.b64decode(imgstr), name=filename)
        return data


class UserSerializer(serializers.ModelSerializer, Base64Image):
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
            "password",
            "is_subscribed",
            "avatar",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Получаем HTTP-метод из контекста
        request = self.context.get('request')
        if request and request.method == 'POST':
            # При POST все поля обязательны
            self.fields['email'].required = True
            self.fields['username'].required = True
            self.fields['first_name'].required = True
            self.fields['last_name'].required = True
            self.fields['password'].required = True
        else:
            # При PUT/PATCH поля необязательны
            self.fields['email'].required = False
            self.fields['username'].required = False
            self.fields['first_name'].required = False
            self.fields['last_name'].required = False
            self.fields['password'].required = False

    def validate(self, data):
        request = self.context.get('request')
        if request and request.method == 'POST':
            required_fields = ['email', 'username', 'first_name', 'last_name', 'password']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise serializers.ValidationError({
                    field: "Обязательное поле." for field in missing_fields
                })
        return data

    def create(self, validated_data):
        # Хеширование пароля
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Хеширование пароля
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
            del validated_data["password"]
        return super().update(instance, validated_data)

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user, author=obj).exists()
        return False

    # Оформление вывода как в API-документации
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        if request and request.method == "POST":
            representation.pop("is_subscribed", None)
            representation.pop("avatar", None)
        return representation

    def get_avatar(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return obj.avatar.url
        return None

    # def to_internal_value(self, data):
    #     data = self.handle_base64_image('avatar', data)
    #     return super().to_internal_value(data)


class AvatarSerializer(serializers.Serializer, Base64Image):
    avatar = serializers.CharField(required=True)

    def validate_avatar(self, value):
        if not value.startswith("data:image"):
            raise serializers.ValidationError(
                "Некорректный формат изображения. Ожидается base64 строка"
            )
        return value

    # def create(self, validated_data):
    #     # Не используется для этого эндпоинта
    #     pass

    def to_internal_value(self, data):
        data = self.handle_base64_image("avatar", data)
        if "avatar" not in data:
            raise serializers.ValidationError({"avatar": "Не удалось обработать изображение"})
        return data

    def update(self, instance, validated_data):
        avatar_file = validated_data['avatar']
        
        if instance.avatar:
            instance.avatar.delete()
        
        instance.avatar.save(
            avatar_file.name,
            avatar_file,
            save=True
        )
        instance.save()
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
        source="ingredient", queryset=Ingredient.objects.all()
    )
    name = serializers.StringRelatedField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.StringRelatedField(
        source="ingredient.measurement_unit", read_only=True
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
            return Subscription.objects.filter(user=request.user, author=obj).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return obj.avatar.url
        return None


class RecipeSerializer(serializers.ModelSerializer, Base64Image):
    author = AuthorSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True, source="recipe_ingredients")
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = ("author",)

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Должен быть хотя бы один ингредиент")
        
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Каждый ингредиент должен быть объектом")
            if 'id' not in item or 'amount' not in item:
                raise serializers.ValidationError("Ингредиент должен содержать id и amount")
            if not isinstance(item['amount'], (int, float)) or item['amount'] <= 0:
                raise serializers.ValidationError("Количество должно быть положительным числом")
        
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients")
        recipe = Recipe.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data["ingredient"],
                amount=ingredient_data["amount"],
            )

        return recipe

    def to_internal_value(self, data):
        # Обработка изображения
        data = self.handle_base64_image("image", data)
        
        # Обработка ингредиентов
        if 'ingredients' in data:
            try:
                # Поддержка строки JSON
                if isinstance(data['ingredients'], str):
                    try:
                        data['ingredients'] = json.loads(data['ingredients'])
                    except json.JSONDecodeError:
                        raise serializers.ValidationError({
                            'ingredients': 'Невалидный JSON формат'
                        })
                
                # Проверка типа
                if not isinstance(data['ingredients'], list):
                    raise serializers.ValidationError({
                        'ingredients': 'Ожидается массив объектов'
                    })
                
                # Преобразование ингредиентов
                recipe_ingredients = []
                for item in data['ingredients']:
                    if not isinstance(item, dict):
                        raise serializers.ValidationError({
                            'ingredients': 'Каждый ингредиент должен быть объектом'
                        })
                    
                    # Извлечение ID ингредиента
                    ingredient_id = None
                    if isinstance(item.get('id'), int):
                        ingredient_id = item['id']
                    elif isinstance(item.get('ingredient'), int):
                        ingredient_id = item['ingredient']
                    elif hasattr(item.get('ingredient'), 'id'):
                        ingredient_id = item['ingredient'].id
                    
                    # Извлечение количества
                    amount = item.get('amount')
                    
                    # Валидация
                    if not ingredient_id or not isinstance(ingredient_id, int):
                        raise serializers.ValidationError({
                            'ingredients': 'ID ингредиента должен быть числом'
                        })
                    
                    if not amount or not isinstance(amount, (int, float)) or amount <= 0:
                        raise serializers.ValidationError({
                            'ingredients': 'Количество должно быть положительным числом'
                        })
                    
                    recipe_ingredients.append({
                        'ingredient': ingredient_id,
                        'amount': amount
                    })
                
                data['recipe_ingredients'] = recipe_ingredients
                del data['ingredients']
                
            except Exception as e:
                raise serializers.ValidationError({
                    'ingredients': str(e)
                })
        
        return super().to_internal_value(data)

    def validate(self, data):
        if 'recipe_ingredients' not in data or not data['recipe_ingredients']:
            raise serializers.ValidationError({
                'ingredients': 'Должен быть хотя бы один ингредиент'
            })
        return data

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        if ingredients_data is None:
            raise serializers.ValidationError(
                {'ingredients': 'Поле обязательно для обновления'}
            )

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        
        # Обновляем изображение если оно передано
        if 'image' in validated_data:
            instance.image = validated_data['image']
        
        # Сохраняем изменения рецепта
        instance.save()

        # Обновляем ингредиенты
        instance.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=instance,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        ])
        
        return instance
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['ingredients'] = [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
                'amount': ri.amount
            }
            for ri in instance.recipe_ingredients.select_related('ingredient')
        ]
        if instance.image:
            ret['image'] = instance.image.url
        return ret

    


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

    class Meta:
        model = Subscription
        fields = ("user", "following", "recipes", "recipes_count")

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        queryset = obj.following.recipes.all()
        if limit:
            queryset = queryset[: int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()
