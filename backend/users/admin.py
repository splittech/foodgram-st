from django.contrib.auth import get_user_model
from django.contrib import admin
from recipes.models import Recipe

User = get_user_model()


class RecipesInLine(admin.TabularInline):
    model = Recipe
    fk_name = 'author'
    verbose_name = 'Рецепт'
    verbose_name_plural = 'Рецепты'
    exclude = ('users_favorited', 'users_added_to_shopping_cart')

    def ingredients_list(self, instance):
        return ', '.join([
            f'{ingredient.ingredient_id.name} '
            f'({ingredient.amount} '
            f'{ingredient.ingredient_id.measurement_unit})'
            for ingredient in instance.ingredients.all()
        ])
    ingredients_list.short_description = 'Ингредиенты'

    readonly_fields = ('name', 'text', 'cooking_time',
                       'image', 'ingredients_list')

    def get_extra(self, request, obj=None, **kwargs):
        extra = 1
        if obj:
            return extra - obj.recipes.count()
        return extra


class UserAdmin(admin.ModelAdmin):
    model = User
    inlines = (RecipesInLine,)
    search_fields = ('username', 'email')


admin.site.register(User, UserAdmin)
