"""Filtering for the game list endpoint."""

from django.utils import timezone
from django_filters import rest_framework as filters

from core.filters import GenreFilterSet

from .models import Game


class GameFilterSet(GenreFilterSet):
    STATUS_CHOICES = [("upcoming", "Upcoming"), ("released", "Released")]

    platform = filters.CharFilter(method="filter_platform")
    release_date_gte = filters.DateFilter(field_name="release_date", lookup_expr="gte")
    release_date_lte = filters.DateFilter(field_name="release_date", lookup_expr="lte")
    status = filters.ChoiceFilter(choices=STATUS_CHOICES, method="filter_status")
    rating_gte = filters.NumberFilter(field_name="rating", lookup_expr="gte")

    class Meta:
        model = Game
        fields = ["genre", "platform", "release_date_gte", "release_date_lte", "status", "rating_gte"]

    def filter_platform(self, queryset, name, value):
        value = value.strip()
        return queryset.filter(platforms__contains=[value]) if value else queryset

    def filter_status(self, queryset, name, value):
        today = timezone.localdate()
        if value == "upcoming":
            return queryset.filter(release_date__gt=today)
        if value == "released":
            return queryset.filter(release_date__lte=today)
        return queryset
