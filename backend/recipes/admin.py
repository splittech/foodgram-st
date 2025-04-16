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
        return instance.ingredient_id.measurement_unit
    measurement_unit.short_description = 'Единица измерения'

    readonly_fields = ('measurement_unit',)


class RecipeAdmin(admin.ModelAdmin):
    model = models.Recipe
    inlines = (IngredientsInLine,)
    search_fields = ('author__username', 'name')
    exclude = ('users_favorited',)

    def favorites_count(self, obj):
        return obj.users_favorited.count()
    favorites_count.short_description = 'В избранном (количество)'

    list_display = ('name', 'favorites_count',)
    readonly_fields = ('favorites_count',)


class IngredientAdmin(admin.ModelAdmin):
    model = models.Ingredient
    search_fields = ('name',)


admin.site.register(models.Recipe, RecipeAdmin)
admin.site.register(models.Ingredient, IngredientAdmin)
admin.site.register(models.RecipeIngredient)
admin.site.register(models.ShortLink)
