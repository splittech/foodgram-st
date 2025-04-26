from django_filters.rest_framework import FilterSet, NumberFilter

from .models import Recipe


class RecipeFilter(FilterSet):
    is_favorited = NumberFilter(method="filter_is_favorited")
    is_in_shopping_cart = NumberFilter(method="filter_is_in_shopping_cart")
    author = NumberFilter(field_name="author__id")

    class Meta:
        model = Recipe
        fields = ("author", "is_favorited", "is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(shoppingcart__user=self.request.user)
        return queryset
