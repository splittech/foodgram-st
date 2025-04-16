from django.core.files.base import ContentFile
from rest_framework import serializers
from django.contrib.auth import get_user_model
import re

import base64

from recipes.models import Recipe

User = get_user_model()


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


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для пользователей.
    """
    # Устанавливаем пароль как поле только для записи,
    # чтобы он обрабатывался при создании пользвателя.
    password = serializers.CharField(write_only=True, required=True)
    # Получаем картинку аватара из base64 в запросе.
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar', 'password')

    def validate_username(self, value):
        # Проверка на соответсвие структуре для имени пользователя.
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                'Неподходящий формат имени пользователя.'
            )
        return value


class ChangePasswordSerializer(serializers.Serializer):

    current_password = serializers.CharField()
    new_password = serializers.CharField()

    class Meta:
        field = '__all__'


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Дополнительный сериализатор для рецепта c меньшим набором полей.
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserWithRecipesSerializer(serializers.ModelSerializer):
    """
    Дополнительный сериализатор для пользователя,
    включающий список рецептов и их количество.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()

        if limit is not None:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                raise serializers.ValidationError(
                    'Параметр ограничения для рецептов - не число'
                )

        return ShortRecipeSerializer(recipes, many=True).data
