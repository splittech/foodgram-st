from django.conf import settings

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics, ttfonts
from collections import defaultdict
import os

from .models import RecipeIngredient


def create_recipe_ingredients_from_request_data(ingredients_data, recipe):
    """
    Функция производит операцию создания ингридиентов рецепта,
    используя данные из запроса.
    """
    for ingredient_data in ingredients_data:
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient_id_id=ingredient_data.get('id'),
            amount=ingredient_data.get('amount')
        )


def get_short_link(code):
    return f'https://127.0.0.1:8000/s/{code}'


def get_pdf_from_recipe_list(buffer, recipes):
    """
    Функция принимет queryset рецептов и заполняет буфер данными,
    представляющими собой список покупок в формате pdf.
    Используем библиотеку reportlab для работы с pdf.
    """

    # Устанавливаем новый шрифт, так как по-умолчанию
    # русский язык не поддерживается.
    font_path = os.path.join(settings.STATIC_ROOT, 'ComicSansMS.ttf')
    pdfmetrics.registerFont(ttfonts.TTFont('ComicSansMS', font_path))

    # Создаем PDF-файл в памяти.
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Заголовок.
    pdf.setFont('ComicSansMS', 16)
    pdf.drawCentredString(width / 2, height - 40, 'Список покупок')

    # Основной текст.
    y = height - 80
    pdf.setFont('ComicSansMS', 12)

    # Составляем словарь с различными ингредиентами, суммируя количество.
    distinct_ingredients = defaultdict(
        lambda: {'amount': 0, 'measurement_units': ''}
    )

    for recipe in recipes:
        ingredients = RecipeIngredient.objects.filter(recipe=recipe)

        for ingredient in ingredients:
            ingredient_name = ingredient.ingredient_id.name
            distinct_ingredients[ingredient_name]['measurement_units'] = \
                ingredient.ingredient_id.measurement_unit
            distinct_ingredients[ingredient_name]['amount'] += \
                ingredient.amount

    for name, data in distinct_ingredients.items():
        pdf.drawString(
            50,
            y,
            f'• {name} ({data["measurement_units"]})'
            f' – {data["amount"]}'
        )
        y -= 20
        if y < 50:
            pdf.showPage()
            y = height - 40

    pdf.save()
