from django.contrib import admin
from .models import (
    Ingredient, Recipe, 
    RecipeIngredient, Favorite, 
    ShoppingCart, Subscription)


class RecipeIngredientInline(admin.StackedInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1 


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    search_fields = ('name', 'author__username')
    inlines = [RecipeIngredientInline]

    readonly_fields = ('favorites_count_display','pub_date' )

    fieldsets = (
        (None, {
            'fields': ('name', 'author',)
        }),
        ('Статистика', {
            'fields': ('favorites_count_display',)
        }),
        ('Детали рецепта', {
            'fields': ('text', 'cooking_time', 'image', 'pub_date')
        }),
    )

    def favorites_count_display(self, obj):
        return obj.favorites_count
    favorites_count_display.short_description = 'Добавлений в избранное'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


admin.site.empty_value_display = 'Не задано'
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart)
admin.site.register(Subscription)
