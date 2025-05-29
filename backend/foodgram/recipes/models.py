from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator


MAX_VALUE_POSITIVE_SMALL_INT = 32000
MIN_VALUE_POSITIVE_SMALL_INT = 1

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    measurement_unit = models.CharField(
        max_length=50, 
        verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], 
                name="unique_ingredient"
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        related_name="recipes", 
        verbose_name="Автор"
    )
    name = models.CharField(max_length=200, verbose_name="Название")
    image = models.ImageField(
        upload_to="recipes/images/", verbose_name="Картинка",
        null=False, blank=False)
    text = models.TextField(verbose_name="Описание")
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        verbose_name="Ингредиенты"
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления (мин)",
        validators=[
            MaxValueValidator(MAX_VALUE_POSITIVE_SMALL_INT),
            MinValueValidator(MIN_VALUE_POSITIVE_SMALL_INT)
        ]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Дата публикации"
    )

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        

    def __str__(self):
        return self.name
    
    @property
    def favorites_count(self):
        """Количество добавлений в избранное"""
        
        return self.favorites.count() 


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[
            MaxValueValidator(MAX_VALUE_POSITIVE_SMALL_INT),
            MinValueValidator(MIN_VALUE_POSITIVE_SMALL_INT)
        ])

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], 
                name="unique_recipe_ingredient"
            )
        ]
        ordering = ["recipe"]

    def __str__(self):
        return f" {self.recipe}: {self.ingredient} - {self.amount}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart"
            )
        ]
        ordering = ["recipe"]

    def __str__(self):
        return f"{self.user} -> {self.recipe}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        constraints = [
            models.UniqueConstraint(fields=["user", "recipe"], 
                                    name="unique_favorite")
        ]
        ordering = ["recipe"]

    def __str__(self):
        return f"{self.user} -> {self.recipe}"


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        related_name="following", 
        verbose_name="Автор"
    )
 
    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_subscription"
            )
        ]
        ordering = ["author"]

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
