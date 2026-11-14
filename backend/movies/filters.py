"""Filtering for the movie list endpoint."""

from django_filters import rest_framework as filters

from core.filters import GenreFilterSet

from .models import Movie


class MovieFilterSet(GenreFilterSet):
    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("now_showing", "Now showing"),
        ("recent", "Recent"),
    ]

    status = filters.ChoiceFilter(choices=STATUS_CHOICES, method="filter_status")
    year = filters.NumberFilter(field_name="release_date", lookup_expr="year")
    rating_gte = filters.NumberFilter(field_name="rating", lookup_expr="gte")
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Movie
        fields = ["status", "genre", "year", "rating_gte", "search"]

    def filter_status(self, queryset, name, value):
        # queryset is a MovieQuerySet, so the status windows live on the queryset.
        return {
            "upcoming": queryset.upcoming,
            "now_showing": queryset.now_showing,
            "recent": queryset.recent,
        }[value]()

    def filter_search(self, queryset, name, value):
        value = value.strip()
        return queryset.filter(title__icontains=value) if value else queryset
