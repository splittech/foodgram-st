from django.db.models import Exists, OuterRef
from django_filters.rest_framework import FilterSet, BooleanFilter

from .models import Recipe


class RecipeFilter(FilterSet):
    """
    Кастомный фильтр для обработки полей 'is_favorited' и
    'is_in_shopping_cart', которые отсутствуют в модели.
    """
    # Этих полей нет в модели, но фильтрация по ним нужна.
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author')

    # Определяем свои правила фильтрации для полей.
    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        # Добавляем поле как аннотацию помимо основных параметров queryset.
        # Уже после этого фильтруем по данному полю.
        if not user.is_authenticated:
            return queryset
        return queryset.annotate(
            is_favorited=Exists(
                Recipe.objects.filter(
                    # Ссылка на внешний запрос queryset, чтобы рассматривать
                    # только тот объект, на который добавляется аннотация.
                    id=OuterRef('id'),
                    users_favorited=user
                )
            )
        ).filter(is_favorited=value)

    # То же самое.
    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset
        return queryset.annotate(
            is_in_shopping_cart=Exists(
                Recipe.objects.filter(
                    id=OuterRef('id'),
                    users_added_to_shopping_cart=user
                )
            )
        ).filter(is_in_shopping_cart=value)
