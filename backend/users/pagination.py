from rest_framework.pagination import PageNumberPagination


class CustomLimitPagination(PageNumberPagination):
    """
    Собственный пагинатор для динамической
    пагинации на основе параметра limit в запросе.
    """
    def get_page_size(self, request):
        # Параметр limit из запроса.
        limit = request.query_params.get('limit')
        if limit is not None:
            # Проверка на то что параметр - целое число (на всякий).
            try:
                return int(limit)
            except ValueError:
                pass
        # Cтандартное значение.
        return 10
