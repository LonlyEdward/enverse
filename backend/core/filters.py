"""Shared filter building blocks for content list endpoints."""

from django_filters import rest_framework as filters


class GenreFilterSet(filters.FilterSet):
    """Base filterset giving every content list a ``?genre=`` filter.

    Genres are stored as an ``ArrayField`` of the names each source returns
    (TMDB/RAWG/AniList use title case, e.g. "Action", "Science Fiction"). The
    filter matches a single genre with ArrayField ``__contains`` and trims
    surrounding whitespace. The frontend populates the genre dropdown from
    ``meta/genres/`` (Phase 9), so it always sends a canonical name.
    """

    genre = filters.CharFilter(method="filter_genre")

    def filter_genre(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(genres__contains=[value])
