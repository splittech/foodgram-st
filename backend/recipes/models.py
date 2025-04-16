from django.contrib.auth import get_user_model
from django.db import models

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
    users_favorited = models.ManyToManyField(
        User,
        verbose_name='В избранном у пользователей',
        blank=True,
        related_name='favorite_recipes'
    )
    users_added_to_shopping_cart = models.ManyToManyField(
        User,
        verbose_name='В корзине у пользователей',
        blank=True,
        related_name='shopping_cart_recipes'
    )
    name = models.CharField(verbose_name='Название',
                            max_length=256)
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


class Ingredient(models.Model):
    """
    Модель для ингридиентов.
    """
    name = models.CharField(verbose_name='Название',
                            max_length=256)
    measurement_unit = models.CharField(verbose_name='Единицы измерения',
                                        max_length=10)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Отдельная модель ингридиентов для рецепта. Нужна, чтобы хранить разное
    количество ингридиентов для каждого рецепта.
    """
    ingredient_id = models.ForeignKey(Ingredient,
                                      verbose_name='Ингредиент',
                                      on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,
                               verbose_name='Рецепт',
                               on_delete=models.CASCADE,
                               related_name='ingredients')

    amount = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Ингридиент для рецепта'
        verbose_name_plural = 'Ингридиенты для рецепта'

    def __str__(self):
        return f'{self.ingredient_id.name} для {self.recipe.name}'


class ShortLink(models.Model):
    """
    Модель для хранения сокращенных ссылок
    """
    recipe = models.OneToOneField(Recipe, on_delete=models.CASCADE)
    code = models.CharField(max_length=3, unique=True)

    class Meta:
        verbose_name = 'Сокращенная ссылка'
        verbose_name_plural = 'Сокращенные ссылки'
