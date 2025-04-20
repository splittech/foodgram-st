import string
import random
import io

from wsgiref.util import FileWrapper
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.filters import SearchFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)
from django_filters.rest_framework import DjangoFilterBackend

from foodgram_back.constants import SHORT_LINK_CODE_MAX_LENGTH
from users.serializers import ShortRecipeSerializer
from users.pagination import CustomLimitPagination
from . import (permissions,
               serializers,
               filters,
               models,
               utils)


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    Вьюсет для получения списка ингредиентов или одиночного ингредиента.
    """
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(ModelViewSet):
    """
    Вьюсет для работы с рецептами.
    """
    queryset = models.Recipe.objects.all()
    pagination_class = CustomLimitPagination
    permission_classes = (IsAuthenticatedOrReadOnly,
                          permissions.AuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return serializers.RecipeWriteSerializer
        return serializers.RecipeReadSerializer

    def perform_create(self, serializer):

        recipe = serializer.save(author=self.request.user)
        read_serializer = serializers.RecipeReadSerializer(
            recipe, context={'request': self.request}
        )
        self.response_data = read_serializer.data

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(
            self.response_data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        instance = serializer.instance
        response_serializer = serializers.RecipeReadSerializer(
            instance,
            context=self.get_serializer_context()
        )

        return Response(response_serializer.data)


class GetShortLinkView(APIView):
    """
    Представление для получения короткой ссылки на рецепт.
    """
    def get(self, request, pk):
        recipe = get_object_or_404(models.Recipe, pk=pk)
        short_link, _ = models.ShortLink.objects.get_or_create(
            recipe=recipe,
            defaults={'code': self.generate_unique_code()}
        )

        return Response({'short-link': utils.get_short_link(short_link.code)})

    @staticmethod
    def generate_unique_code():
        characters = string.ascii_letters + string.digits
        code_length = SHORT_LINK_CODE_MAX_LENGTH

        while True:
            code = ''.join(random.choices(characters, k=code_length))
            if not models.ShortLink.objects.filter(code=code).exists():
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
    def post(self, request, recipe_id):
        recipe = get_object_or_404(models.Recipe, id=recipe_id)
        serializer = serializers.ShoppingCartSerializer(
            data={
                'user': request.user.id,
                'recipe': recipe.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(models.Recipe, id=recipe_id)
        serializer = serializers.ShoppingCartDeleteSerializer(
            data={
                'user': request.user.id,
                'recipe': recipe.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        cart_item = get_object_or_404(
            models.ShoppingCart,
            user=request.user,
            recipe_id=recipe_id
        )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadShoppingCartView(APIView):
    """
    Представление для того, чтобы скачать список покупок.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        recipes = models.Recipe.objects.filter(
            shoppingcart__user=self.request.user
        ).prefetch_related('recipes')

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
    permission_classes = (IsAuthenticated,)

    def post(self, request, recipe_id):
        recipe = get_object_or_404(models.Recipe, id=recipe_id)
        serializer = serializers.FavoriteSerializer(
            data={
                'user': request.user.id,
                'recipe': recipe.id
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, recipe_id):
        recipe = get_object_or_404(models.Recipe, id=recipe_id)
        serializer = serializers.FavoriteDeleteSerializer(
            data={
                'user': request.user.id,
                'recipe': recipe.id
            },
        )
        serializer.is_valid(raise_exception=True)

        favorite_item = get_object_or_404(
            models.Favorite,
            user=request.user,
            recipe_id=recipe_id
        )
        favorite_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
