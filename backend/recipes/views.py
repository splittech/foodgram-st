from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.filters import SearchFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)

from wsgiref.util import FileWrapper
import string
import random
import io

from users.serializers import ShortRecipeSerializer
from users.pagination import CustomLimitPagination

from . import (permissions,
               serializers,
               filters,
               models,
               utils)


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    Вьюсет для получения списка ингредиентов
    или одного ингредиента по его id.
    """
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(ModelViewSet):
    """
    Вьюсет для работы с моделью рецептов.
    """
    queryset = models.Recipe.objects.all()
    serializer_class = serializers.RecipeSerializer
    pagination_class = CustomLimitPagination
    permission_classes = (IsAuthenticatedOrReadOnly,
                          permissions.AuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilter

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', None)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


class GetShortLinkView(APIView):
    """
    Представление для получения короткой ссылки на рецепт.
    """
    def get(self, request, pk):
        recipe = get_object_or_404(models.Recipe, pk=pk)
        short_link = models.ShortLink.objects.filter(recipe=recipe).first()
        if not short_link:
            # Если ссылки нет, то генерируем код.
            code_list = models.ShortLink.objects.values_list('code', flat=True)
            code = self.generate_code()
            while code in code_list:
                code = self.generate_code()
            short_link = models.ShortLink.objects.create(recipe=recipe,
                                                         code=code)

        return Response({'short-link': utils.get_short_link(short_link.code)})

    def generate_code(self):
        characters = string.ascii_letters + string.digits
        code = ''
        for _ in range(3):
            code += random.choice(characters)
        return code


class ShortLinkView(APIView):
    """
    Представление для обработки короткой ссылки на рецепт.
    """
    def get(self, request, code):
        short_link = get_object_or_404(models.ShortLink, code=code)
        return redirect(f'/recipes/{short_link.recipe.id}')


class ShoppingCartView(APIView):
    """
    Представление для добавления рецепта в список покупок или его удаления.
    """
    def post(self, request, *args, **kwargs):
        recipe = get_object_or_404(models.Recipe, id=kwargs.get('recipe_id'))

        if request.user in recipe.users_added_to_shopping_cart.all():
            return Response({'detail': 'Рецепт уже есть в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        recipe.users_added_to_shopping_cart.add(request.user)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(models.Recipe, id=kwargs.get('recipe_id'))

        if request.user not in recipe.users_added_to_shopping_cart.all():
            return Response({'detail': 'Рецепта не было в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        recipe.users_added_to_shopping_cart.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadShoppingCartView(APIView):
    """
    Представление для того, чтобы скачать список покупок.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        recipes = models.Recipe.objects.filter(
            users_added_to_shopping_cart=request.user
        )

        # Создаем буфер в памяти.
        buffer = io.BytesIO()
        try:
            utils.get_pdf_from_recipe_list(buffer, recipes)
        except MemoryError:
            return Response(
                {'detail': 'Недостаточно памяти для создания pdf.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Перематываем буфер в начало и передаем его в ответ.
        buffer.seek(0)
        return HttpResponse(
            FileWrapper(buffer),
            content_type='application/pdf')


class FavoriteView(APIView):
    """
    Представление для добавления рецепта в избранное или его удаления.
    """
    def post(self, request, *args, **kwargs):
        recipe = get_object_or_404(models.Recipe, id=kwargs.get('recipe_id'))

        if request.user in recipe.users_favorited.all():
            return Response({'detail': 'Рецепт уже находится в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

        recipe.users_favorited.add(request.user)

        # Сериализатор для вывода согласно заданию.
        serializer = serializers.ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(models.Recipe, id=kwargs.get('recipe_id'))

        if request.user not in recipe.users_favorited.all():
            return Response({'detail': 'Рецепта и так не было в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

        recipe.users_favorited.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
