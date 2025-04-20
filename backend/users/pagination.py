from rest_framework.pagination import PageNumberPagination


class CustomLimitPagination(PageNumberPagination):
    """
    Собственный пагинатор для динамической
    пагинации на основе параметра limit в запросе.
    """
    page_size_query_param = 'limit'
