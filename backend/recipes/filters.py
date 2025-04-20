from django_filters.rest_framework import FilterSet, BooleanFilter

from .models import Recipe


class RecipeFilter(FilterSet):
    """
    Фильтр для полей, которые отсутствуют в модели рецептов.
    """
    is_favorited = BooleanFilter(method='filter_by_relation')
    is_in_shopping_cart = BooleanFilter(method='filter_by_relation')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author')

    # Объединил два метода в один.
    def filter_by_relation(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated or not value:
            return queryset

        # Определяем поле фильтрации в зависимости от запрашиваемого параметра.
        relation_map = {
            'is_favorited': 'favorite__user',
            'is_in_shopping_cart': 'shoppingcart__user'
        }

        relation_field = relation_map.get(name)
        if not relation_field:
            return queryset

        # Фильтруем по связи с текущим пользователем.
        return queryset.filter(**{relation_field: user})
