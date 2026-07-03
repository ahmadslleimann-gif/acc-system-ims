from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Default page size 25, but lets the client request more via ?page_size=."""

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 1000
