import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics, ttfonts
from django.conf import settings
from django.urls import reverse
from django.db.models import Sum

from .models import RecipeIngredient


def get_short_link(code):
    """
    Функция формирует короткую ссылку с учетом параметров приложения.
    """
    domain = getattr(settings, 'SITE_URL', '127.0.0.1:8000')

    relative_url = reverse('short_link', kwargs={'code': code})

    scheme = 'https' if settings.SECURE_SSL_REDIRECT else 'http'
    return f'{scheme}://{domain}{relative_url}'


def get_pdf_from_recipe_list(buffer, recipes):
    """
    Функция принимет queryset рецептов и заполняет буфер данными,
    представляющими собой список покупок в формате pdf.
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

    # Получаем все ингредиенты одним запросом с агрегацией и аннотацией.
    ingredients_data = RecipeIngredient.objects.filter(
        recipe__in=recipes
    ).values(
        'ingredient__name',
        'ingredient__measurement_unit'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('ingredient__name')

    for ingredient_data in ingredients_data:
        pdf.drawString(
            50,
            y,
            f'• {ingredient_data["ingredient__name"]}'
            f' ({ingredient_data["ingredient__measurement_unit"]}) '
            f'– {ingredient_data["total_amount"]}'
        )
        y -= 20
        if y < 50:
            pdf.showPage()
            y = height - 40

    pdf.save()
