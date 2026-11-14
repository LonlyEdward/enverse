"""Read-side helpers for movies that are more than a single ORM call."""

from django.db.models import F

from .models import Movie

SIMILAR_LIMIT = 10
_SIMILAR_CANDIDATES = 60  # cap the DB scan; we re-rank these in Python by overlap


def similar_movies(movie, limit=SIMILAR_LIMIT):
    """Return up to ``limit`` movies sharing genres with ``movie``.

    Ranked by number of shared genres, then popularity. Computed locally from
    genre overlap with no extra API calls. Empty if the movie has no genres.
    """
    if not movie.genres:
        return []
    candidates = list(
        Movie.objects.filter(genres__overlap=movie.genres)
        .exclude(pk=movie.pk)
        .order_by(F("popularity").desc(nulls_last=True))[:_SIMILAR_CANDIDATES]
    )
    wanted = {g.casefold() for g in movie.genres}

    def overlap(candidate):
        return len(wanted & {g.casefold() for g in candidate.genres})

    candidates.sort(key=lambda m: (overlap(m), m.popularity or 0.0), reverse=True)
    return candidates[:limit]
