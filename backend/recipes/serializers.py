from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model

from users.serializers import UserSerializer
from . import models

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отдельно ингредиентов.
    """
    class Meta:
        model = models.Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения ингредиентов в рецепте.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = models.RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления ингредиентов в рецепте.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=models.Ingredient.objects.all()
    )

    class Meta:
        model = models.RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количество должно быть больше 0.'
            )
        return value


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения рецептов.
    """
    author = UserSerializer()
    ingredients = RecipeIngredientReadSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        fields = ('id', 'author', 'name', 'text', 'cooking_time',
                  'image', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart')
        read_only_fields = fields

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request:
            return False

        return (
            request.user.is_authenticated
            and obj.favorite.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request:
            return False

        return (
            request.user.is_authenticated
            and obj.shoppingcart.filter(user=request.user).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления и обновления рецептов.
    """
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = models.Recipe
        fields = ('name', 'text', 'cooking_time', 'image', 'ingredients')

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Время готовки должно быть больше 0.'
            )
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Должна быть фотография'
            )
        return value

    def validate_ingredients(self, value):

        if not value:
            raise serializers.ValidationError(
                'Должен быть хотя бы один ингредиент'
            )

        ingredients = [item['id'] for item in value]

        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )

        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = models.Recipe.objects.create(**validated_data)
        self.create_recipe_ingredients(recipe, ingredients_data)

        # Передаем контекст запроса в RecipeReadSerializer
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        self.validate_ingredients(ingredients_data)
        instance = super().update(instance, validated_data)

        instance.ingredients.all().delete()
        self.create_recipe_ingredients(instance, ingredients_data)

        return instance

    @staticmethod
    def create_recipe_ingredients(recipe, ingredients_data):
        """
        Производит создание ингридиентов для рецепта.
        """
        recipe_ingredients = [
            models.RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],  # Используем ingredient_id
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ]

        models.RecipeIngredient.objects.bulk_create(recipe_ingredients)


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        if models.ShoppingCart.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                {'detail': 'Рецепт уже в списке покупок'}
            )
        return data


class ShoppingCartDeleteSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        if not models.ShoppingCart.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                {'detail': 'Рецепт и так не был в списке покупок'}
            )
        return data


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Favorite
        fields = ('user', 'recipe')
        extra_kwargs = {
            'user': {'write_only': True},
            'recipe': {'write_only': True}
        }

    def validate(self, data):
        if models.Favorite.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                {'detail': 'Рецепт уже в избранном'}
            )
        return data


class FavoriteDeleteSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        if not models.Favorite.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                {'detail': 'рецепт и так не был в избранном'}
            )
        return data
