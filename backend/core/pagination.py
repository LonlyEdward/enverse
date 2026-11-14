"""Shared pagination for the whole API."""

from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Page-number pagination: 20 per page, caller may request up to 100.

    A capped ``page_size`` query param lets the frontend ask for larger pages
    (e.g. a calendar month) without letting a client request unbounded rows.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
