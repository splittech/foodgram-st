from django.contrib import admin
from django.contrib.auth import get_user_model

from . import models

User = get_user_model()


class IngredientsInLine(admin.TabularInline):
    model = models.RecipeIngredient
    fk_name = 'recipe'
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'

    def measurement_unit(self, instance):
        return instance.ingredient.measurement_unit
    measurement_unit.short_description = 'Единица измерения'

    readonly_fields = ('measurement_unit',)


class RecipeAdmin(admin.ModelAdmin):
    model = models.Recipe
    inlines = (IngredientsInLine,)
    search_fields = ('author__username', 'name')

    list_display = ('name', 'author', 'pub_date', 'favorites_count')
    readonly_fields = ('favorites_count',)

    def favorites_count(self, obj):
        return obj.favorite.count()
    favorites_count.short_description = 'В избранном (количество)'


class IngredientAdmin(admin.ModelAdmin):
    model = models.Ingredient
    search_fields = ('name',)


admin.site.register(models.Recipe, RecipeAdmin)
admin.site.register(models.Ingredient, IngredientAdmin)
admin.site.register(models.ShortLink)
admin.site.register(models.Favorite)
admin.site.register(models.ShoppingCart)
