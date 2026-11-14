"""Filtering for the anime list endpoint."""

from django_filters import rest_framework as filters

from core.filters import GenreFilterSet

from .models import Anime


class AnimeFilterSet(GenreFilterSet):
    studio = filters.CharFilter(method="filter_studio")
    airing_status = filters.ChoiceFilter(choices=Anime.AiringStatus.choices)
    season = filters.ChoiceFilter(choices=Anime.Season.choices)
    season_year = filters.NumberFilter()
    rating_gte = filters.NumberFilter(field_name="rating", lookup_expr="gte")

    class Meta:
        model = Anime
        fields = ["genre", "studio", "airing_status", "season", "season_year", "rating_gte"]

    def filter_studio(self, queryset, name, value):
        value = value.strip()
        return queryset.filter(studios__contains=[value]) if value else queryset
