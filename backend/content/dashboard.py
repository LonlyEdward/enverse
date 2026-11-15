"""The personalised dashboard: one authenticated call that returns every home
section. Each section is capped and genre-aware (with a popular fallback), and the
query count stays flat regardless of how much content or library a user has.
"""

from collections import defaultdict
from datetime import datetime, time, timedelta, timezone as dt_timezone

from django.db.models import F, Q
from django.utils import timezone

from accounts.models import GenrePreference
from anime.models import Anime
from core.registry import load_content, summarize
from games.models import Game
from library.models import Favorite, Following
from movies.models import Movie
from notifications.models import Notification
from recommendations.models import Recommendation
from sports.models import FootballFixture
from tv.models import TVShow

SECTION_LIMIT = 10
FAVORITES_WINDOW_DAYS = 14


def _user_genres(user):
    genres = defaultdict(set)
    for content_type, genre in GenrePreference.objects.filter(user=user).values_list("content_type", "genre"):
        genres[content_type].add(genre)
    return genres


def _personalised(base_qs, content_type, user_genres, limit=SECTION_LIMIT):
    """Prefer items matching the user's genres for this type; fall back to popular."""
    genres = user_genres.get(content_type)
    if genres:
        matched = list(base_qs.filter(genres__overlap=list(genres))[:limit])
        if matched:
            return matched
    return list(base_qs[:limit])


def _fixture_row(fixture):
    return {
        "content_type": "football",
        "id": fixture.id,
        "title": f"{fixture.home_team.name} vs {fixture.away_team.name}",
        "poster_url": fixture.home_team.logo_url,
        "kind": "match",
        "datetime": fixture.kickoff_at.isoformat(),
    }


def build_dashboard(user):
    today = timezone.localdate()
    now = timezone.now()
    genres = _user_genres(user)

    in_cinemas = _personalised(
        Movie.objects.filter(release_date__isnull=False, release_date__lte=today).order_by("-release_date"),
        "movie", genres,
    )
    upcoming_movies = _personalised(
        Movie.objects.filter(release_date__gt=today).order_by("release_date"), "movie", genres
    )
    upcoming_tv = _personalised(
        TVShow.objects.filter(next_episode_air_date__gte=today).order_by("next_episode_air_date"), "tv", genres
    )
    anime_airing = _personalised(
        Anime.objects.filter(airing_status=Anime.AiringStatus.RELEASING).order_by(
            F("next_airing_at").asc(nulls_last=True)
        ),
        "anime", genres,
    )
    upcoming_games = _personalised(
        Game.objects.filter(release_date__gt=today).order_by("release_date"), "game", genres
    )

    return {
        "in_cinemas": [summarize(obj) for obj in in_cinemas],
        "upcoming_movies": [summarize(obj) for obj in upcoming_movies],
        "upcoming_tv": [summarize(obj) for obj in upcoming_tv],
        "anime_airing": [summarize(obj) for obj in anime_airing],
        "upcoming_games": [summarize(obj) for obj in upcoming_games],
        "my_fixtures": _my_fixtures(user, now),
        "favorites_updates": _favorites_updates(user, today, now),
        "recommendations": _recommendations(user),
        "unread_notifications": Notification.objects.filter(
            user=user, channel=Notification.Channel.IN_APP, read_at__isnull=True
        ).count(),
    }


def _my_fixtures(user, now):
    team_ids = list(
        Following.objects.filter(user=user, content_type="football").values_list("object_id", flat=True)
    )
    if not team_ids:
        return []
    fixtures = (
        FootballFixture.objects.select_related("home_team", "away_team")
        .filter(
            Q(home_team_id__in=team_ids) | Q(away_team_id__in=team_ids),
            kickoff_at__gte=now,
            status=FootballFixture.Status.SCHEDULED,
        )
        .order_by("kickoff_at")[:SECTION_LIMIT]
    )
    return [_fixture_row(fixture) for fixture in fixtures]


def _favorites_updates(user, today, now):
    """Upcoming events in the next 14 days for favorited or followed items."""
    window_end = today + timedelta(days=FAVORITES_WINDOW_DAYS)
    by_type = defaultdict(set)
    for model in (Favorite, Following):
        for content_type, object_id in model.objects.filter(user=user).values_list("content_type", "object_id"):
            by_type[content_type].add(object_id)

    rows = []
    for content_type, model in (("movie", Movie), ("game", Game)):
        ids = by_type.get(content_type)
        if ids:
            for obj in model.objects.filter(id__in=ids, release_date__gte=today, release_date__lte=window_end):
                rows.append(_dated_row(obj, content_type, "release", obj.release_date.isoformat()))

    tv_ids = by_type.get("tv")
    if tv_ids:
        for show in TVShow.objects.filter(
            id__in=tv_ids, next_episode_air_date__gte=today, next_episode_air_date__lte=window_end
        ):
            rows.append(_dated_row(show, "tv", "episode", show.next_episode_air_date.isoformat()))

    anime_ids = by_type.get("anime")
    if anime_ids:
        end_dt = datetime.combine(window_end, time.max, tzinfo=dt_timezone.utc)
        for anime in Anime.objects.filter(id__in=anime_ids, next_airing_at__gte=now, next_airing_at__lte=end_dt):
            rows.append(_dated_row(anime, "anime", "episode", anime.next_airing_at.isoformat()))

    team_ids = by_type.get("football")
    if team_ids:
        end_dt = datetime.combine(window_end, time.max, tzinfo=dt_timezone.utc)
        fixtures = FootballFixture.objects.select_related("home_team", "away_team").filter(
            Q(home_team_id__in=team_ids) | Q(away_team_id__in=team_ids), kickoff_at__gte=now, kickoff_at__lte=end_dt
        )
        for fixture in fixtures:
            rows.append(_fixture_row(fixture))

    rows.sort(key=lambda row: row.get("datetime") or row.get("date") or "")
    return rows[:SECTION_LIMIT]


def _dated_row(obj, content_type, kind, when):
    return {
        "content_type": content_type,
        "id": obj.id,
        "title": obj.title,
        "poster_url": obj.poster_url,
        "kind": kind,
        "date": when,
    }


def _recommendations(user):
    rows = list(Recommendation.objects.filter(user=user).order_by("-score")[:SECTION_LIMIT])
    items = load_content([(row.content_type, row.object_id) for row in rows])
    out = []
    for row in rows:
        content = items.get((row.content_type, row.object_id))
        out.append(
            {
                "content_type": row.content_type,
                "object_id": row.object_id,
                "reason": row.reason,
                "item": summarize(content) if content is not None else None,
            }
        )
    return out
