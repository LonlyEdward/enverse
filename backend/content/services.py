"""Cross-content discovery: search, trending and genre metadata.

These read across every content type through ``core.registry``. Search also covers
football **team names**, which are not ``SyncedContent`` (no title/popularity), so
teams are handled in their own branch rather than forced through the shared path.
"""

from django.db.models import Case, F, IntegerField, Value, When
from django.utils import timezone

from core.registry import CONTENT_TYPES, get_content_model, summarize

# Content types search spans: the four SyncedContent types plus football teams.
SEARCH_TYPES = CONTENT_TYPES + ("football",)

# Caps so one type cannot crowd the others out of a unified result list, and so a
# trending section stays a short, dashboard-sized slice.
SEARCH_PER_TYPE_LIMIT = 10
TRENDING_LIMIT = 10

MIN_QUERY_LENGTH = 2


def _prefix_rank(field, query):
    """0 for titles that *start with* the query, 1 for the rest, so prefix hits sort first."""
    return Case(
        When(**{f"{field}__istartswith": query}, then=Value(0)),
        default=Value(1),
        output_field=IntegerField(),
    )


def _search_content_type(content_type, query, limit):
    model = get_content_model(content_type)
    rows = (
        model.objects.filter(title__icontains=query)
        .annotate(prefix_rank=_prefix_rank("title", query))
        # Prefix matches first, then most popular; NULL popularity sorts last.
        .order_by("prefix_rank", F("popularity").desc(nulls_last=True), "title")[:limit]
    )
    return [summarize(obj) for obj in rows]


def _search_teams(query, limit):
    from sports.models import FootballTeam

    rows = (
        FootballTeam.objects.filter(name__icontains=query)
        .annotate(prefix_rank=_prefix_rank("name", query))
        .order_by("prefix_rank", "name")[:limit]
    )
    return [summarize(obj) for obj in rows]


def search(query, type_filter=None):
    """Return unified summary rows for ``query`` across one or all content types.

    Each type contributes at most ``SEARCH_PER_TYPE_LIMIT`` rows; types are emitted
    in a stable order (movie, tv, anime, game, football). The caller guarantees the
    query is already length-validated.
    """
    types = [type_filter] if type_filter else SEARCH_TYPES
    results = []
    for content_type in types:
        if content_type == "football":
            results.extend(_search_teams(query, SEARCH_PER_TYPE_LIMIT))
        else:
            results.extend(_search_content_type(content_type, query, SEARCH_PER_TYPE_LIMIT))
    return results


def trending():
    """Top items per content type by ``trending_rank``, plus upcoming fixtures.

    The four content sections are summary rows; ``football`` is a list of soon
    kicking-off scheduled fixtures (richer than a summary) and is serialized by the
    caller, so this returns the fixture queryset for that key.
    """
    from sports.models import FootballFixture

    sections = {}
    for content_type in CONTENT_TYPES:
        model = get_content_model(content_type)
        rows = model.objects.filter(trending_rank__isnull=False).order_by("trending_rank")[:TRENDING_LIMIT]
        sections[content_type] = [summarize(obj) for obj in rows]

    fixtures = (
        FootballFixture.objects.select_related("home_team", "away_team")
        .filter(kickoff_at__gte=timezone.now(), status=FootballFixture.Status.SCHEDULED)
        .order_by("kickoff_at")[:TRENDING_LIMIT]
    )
    return sections, fixtures


def distinct_genres(content_type):
    """Sorted, de-duplicated genre names present in the data for one content type."""
    model = get_content_model(content_type)
    seen = set()
    for genres in model.objects.values_list("genres", flat=True):
        seen.update(genres or [])
    return sorted(seen)
