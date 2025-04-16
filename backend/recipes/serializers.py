from django.core.files.base import ContentFile
from rest_framework import serializers

import base64

from users.serializers import UserSerializer

from . import models, utils


class Base64ImageField(serializers.ImageField):
    """
    Поле сериализатора для обработки изображений, закодированных в base64.
    Взято из теории курса яндекса.
    """
    def to_internal_value(self, data):
        # Если полученный объект строка, и эта строка
        # начинается с 'data:image'...
        if isinstance(data, str) and data.startswith('data:image'):
            # ...начинаем декодировать изображение из base64.
            # Сначала нужно разделить строку на части.
            format, imgstr = data.split(';base64,')
            # И извлечь расширение файла.
            ext = format.split('/')[-1]
            # Затем декодировать сами данные и поместить результат в файл,
            # которому дать название по шаблону.
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингридиентов.
    """
    class Meta:
        model = models.Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор ингридиентов для рецептов.
    """
    id = serializers.ReadOnlyField(source='ingredient_id.id')
    name = serializers.ReadOnlyField(source='ingredient_id.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient_id.measurement_unit')
    amount = serializers.ReadOnlyField(required=False, allow_null=True)

    class Meta:
        model = models.RecipeIngredient
        exclude = ('ingredient_id', 'recipe')


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для рецептов.
    """
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        exclude = ('users_favorited', 'users_added_to_shopping_cart',
                   'pub_date')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.users_favorited.filter(id=request.user.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.users_added_to_shopping_cart.filter(
                id=request.user.id).exists()
        return False

    def validate_cooking_time(self, value):
        if value == 0:
            raise serializers.ValidationError('Не может быть 0.')
        return value

    def validate(self, data):
        ingredients_data = self.initial_data.get('ingredients')
        if not ingredients_data:
            raise serializers.ValidationError(
                {'ingredients': 'Обязательное поле.'}
            )

        ingredient_ids = [ingredient['id'] for ingredient in ingredients_data]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Есть повторения.'}
            )

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            ingredient_amount = ingredient_data.get('amount')

            if not ingredient_id:
                raise serializers.ValidationError(
                    {'ingredient_id': 'Обязательное поле.'}
                )

            if not ingredient_amount:
                raise serializers.ValidationError(
                    {'ingredient_amount': 'Обязательное поле.'}
                )

            if not models.Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    {'ingredient_id': 'Ингридиентов не существует.'}
                )

        return data

    def create(self, validated_data):
        # Удаляем ненужное поле 'ингредиенты',
        # чтобы не было ошибки при обновлении рецептов.
        validated_data.pop('ingredients', None)
        recipe = models.Recipe.objects.create(**validated_data)
        # Создаем объекты связывающей модели для ингредиентов с количеством.
        ingredients_data = self.initial_data.get('ingredients')
        utils.create_recipe_ingredients_from_request_data(
            ingredients_data,
            recipe
        )

        return recipe

    def update(self, instance, validated_data):
        # Удаляем ненужное поле 'ингредиенты',
        # чтобы не было ошибки при обновлении рецептов.
        ingredients_data = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        # Удаляем старые ингредиенты.
        instance.ingredients.all().delete()
        # Создаем новые ингредиенты.
        ingredients_data = self.initial_data.get('ingredients')
        utils.create_recipe_ingredients_from_request_data(
            ingredients_data,
            instance
        )

        return instance


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Дополнительный сериализатор для рецепта c меньшим набором полей.
    """
    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
