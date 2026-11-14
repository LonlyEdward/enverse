"""Filtering for the TV list endpoint."""

from django_filters import rest_framework as filters

from core.filters import GenreFilterSet

from .models import TVShow


class TVFilterSet(GenreFilterSet):
    status = filters.ChoiceFilter(choices=TVShow.Status.choices)
    rating_gte = filters.NumberFilter(field_name="rating", lookup_expr="gte")

    class Meta:
        model = TVShow
        fields = ["genre", "status", "rating_gte"]
