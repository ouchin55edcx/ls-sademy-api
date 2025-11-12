"""
Shared pagination classes for the API.
"""
from rest_framework.pagination import PageNumberPagination


class DefaultPageNumberPagination(PageNumberPagination):
    """
    Default pagination used across the project to keep list endpoints consistent.
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 50

