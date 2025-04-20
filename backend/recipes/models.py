from django.contrib.auth import get_user_model
from django.db import models

from foodgram_back.constants import (RECIPE_INGREDIENT_NAME_MAX_LENGTH,
                                     SHORT_LINK_CODE_MAX_LENGTH,
                                     MEASUREMENT_UNIT_MAX_LENGTH)

User = get_user_model()


class Recipe(models.Model):
    """
    Модель для рецепта.
    """
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(verbose_name='Название',
                            max_length=RECIPE_INGREDIENT_NAME_MAX_LENGTH)
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(verbose_name='Время готовки',
                                               help_text='В минутах')
    image = models.ImageField(verbose_name='Изображение',
                              blank=True, null=True)

    pub_date = models.DateTimeField(verbose_name='Дата публикации',
                                    auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeUser(models.Model):
    """
    Абстрактная модель для реализации отношения рецептом и пользователем.
    """
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='%(class)s'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)s'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='%(class)s_unique_recipe_user'
            )
        ]

    def __str__(self):
        return f'{self.recipe.name} у {self.user.username}'


class Favorite(RecipeUser):
    """
    Модель для избранного.
    """
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(RecipeUser):
    """
    Модель для списка покупок.
    """
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class Ingredient(models.Model):
    """
    Модель для ингридиентов.
    """
    name = models.CharField(verbose_name='Название',
                            max_length=RECIPE_INGREDIENT_NAME_MAX_LENGTH)
    measurement_unit = models.CharField(verbose_name='Единицы измерения',
                                        max_length=MEASUREMENT_UNIT_MAX_LENGTH)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_and_measurement_unit'
            )
        ]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Отдельная модель ингредиентов для рецепта, создержащая количество.
    """
    ingredient = models.ForeignKey(Ingredient,
                                   verbose_name='Ингредиент',
                                   on_delete=models.CASCADE)

    recipe = models.ForeignKey(Recipe,
                               verbose_name='Рецепт',
                               on_delete=models.CASCADE,
                               related_name='ingredients')

    amount = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Ингредиент для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'

        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient_in_recipe'
            ),
        ]

    def __str__(self):
        return f'{self.ingredient.name} для {self.recipe.name}'


class ShortLink(models.Model):
    """
    Модель для хранения сокращенных ссылок.
    """
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)
    code = models.CharField(max_length=SHORT_LINK_CODE_MAX_LENGTH, unique=True)

    class Meta:
        verbose_name = 'Сокращенная ссылка'
        verbose_name_plural = 'Сокращенные ссылки'

    def __str__(self):
        return self.code
