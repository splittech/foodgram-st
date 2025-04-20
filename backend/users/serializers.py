import re

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Recipe
from . import models

User = get_user_model()


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


class UserCreateSerializer(DjoserUserSerializer):
    """
    Отдельный сериализатор для обработки
    запроса на создание пользователя.
    """
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')
        read_only_fields = ('id',)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким атрибутом уже существует'
            )
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким атрибутом уже существует'
            )
        # Проверка на соответсвие структуре для имени пользователя.
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                'Неподходящий формат имени пользователя.'
            )
        return value

    def create(self, validated_data):
        # Вручную создаем пользователя
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=True
        )
        user.password = make_password(validated_data['password'])
        user.save()
        return user


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


class UserAvatarSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления или удаления аватара.
    """
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Сериализатор для валидации изменения пароля пользователя.
    """
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Неверный пароль')
        return value


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Subscription
        exclude = ('id',)

    def validate(self, data):
        author = data.get('author')
        subscriber = data.get('subscriber')

        if author == subscriber:
            raise serializers.ValidationError('Нельзя подписаться на себя')

        if models.Subscription.objects.filter(
            author=author, subscriber=subscriber
        ).exists():
            raise serializers.ValidationError('Уже подписан')

        return data


class UnsubscribeSerializer(serializers.Serializer):
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    subscriber = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def validate(self, data):
        author = data['author']
        subscriber = data['subscriber']

        if author == subscriber:
            raise serializers.ValidationError('Нельзя отписаться от себя')

        if not models.Subscription.objects.filter(
            author=author,
            subscriber=subscriber
        ).exists():
            raise serializers.ValidationError(
                'И так не подписан на этого пользователя'
            )

        return data
