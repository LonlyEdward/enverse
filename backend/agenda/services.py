"""A unified dated-events calendar across every content type.

One function per source, registered in :data:`SOURCES` keyed by content type, so
adding a source is a single function. Each returns a list of row dicts already
shaped for the API. ``mine`` narrows every source to the user's library.
"""

from datetime import datetime, time, timezone as dt_timezone

from django.utils import timezone

from anime.models import Anime, AnimeEpisode
from games.models import Game
from library.models import Favorite, Following, WatchlistItem
from movies.models import Movie
from sports.models import FootballFixture
from tv.models import TVSeason, TVShow

MAX_SPAN_DAYS = 62
LIMIT_PER_SOURCE = 300


def _row(content_type, obj_id, title, poster_url, kind, *, date=None, moment=None):
    """One calendar row. ``moment`` is an aware datetime (UTC); ``date`` a plain date."""
    if moment is not None and date is None:
        date = timezone.localtime(moment, dt_timezone.utc).date()
    return {
        "content_type": content_type,
        "id": obj_id,
        "title": title,
        "poster_url": poster_url,
        "kind": kind,
        "date": date,
        "datetime": moment,
    }


def _owned_ids(user, content_type):
    """Local ids of items the user keeps in their library for one content type."""
    ids = set()
    for model in (Favorite, Following, WatchlistItem):
        ids.update(
            model.objects.filter(user=user, content_type=content_type).values_list("object_id", flat=True)
        )
    return ids


def _released(model, content_type, start, end, user, mine):
    qs = model.objects.filter(release_date__gte=start, release_date__lte=end)
    if mine:
        qs = qs.filter(id__in=_owned_ids(user, content_type))
    return [
        _row(content_type, obj.id, obj.title, obj.poster_url, "release", date=obj.release_date)
        for obj in qs[:LIMIT_PER_SOURCE]
    ]


def movie_source(start, end, user, mine):
    return _released(Movie, "movie", start, end, user, mine)


def game_source(start, end, user, mine):
    return _released(Game, "game", start, end, user, mine)


def tv_source(start, end, user, mine):
    owned = _owned_ids(user, "tv") if mine else None
    rows = []

    episodes = TVShow.objects.filter(next_episode_air_date__gte=start, next_episode_air_date__lte=end)
    seasons = TVSeason.objects.select_related("show").filter(air_date__gte=start, air_date__lte=end)
    if mine:
        episodes = episodes.filter(id__in=owned)
        seasons = seasons.filter(show_id__in=owned)

    for show in episodes[:LIMIT_PER_SOURCE]:
        rows.append(_row("tv", show.id, show.title, show.poster_url, "episode", date=show.next_episode_air_date))
    for season in seasons[:LIMIT_PER_SOURCE]:
        show = season.show
        rows.append(_row("tv", show.id, show.title, show.poster_url, "release", date=season.air_date))
    return rows


def anime_source(start, end, user, mine):
    owned = _owned_ids(user, "anime") if mine else None
    start_dt = _start_of_day(start)
    end_dt = _end_of_day(end)
    rows = []

    upcoming = Anime.objects.filter(next_airing_at__gte=start_dt, next_airing_at__lte=end_dt)
    episodes = AnimeEpisode.objects.select_related("anime").filter(
        aired_at__gte=start_dt, aired_at__lte=end_dt
    )
    if mine:
        upcoming = upcoming.filter(id__in=owned)
        episodes = episodes.filter(anime_id__in=owned)

    for anime in upcoming[:LIMIT_PER_SOURCE]:
        rows.append(_row("anime", anime.id, anime.title, anime.poster_url, "episode", moment=anime.next_airing_at))
    for episode in episodes[:LIMIT_PER_SOURCE]:
        anime = episode.anime
        rows.append(_row("anime", anime.id, anime.title, anime.poster_url, "episode", moment=episode.aired_at))
    return rows


def football_source(start, end, user, mine):
    start_dt = _start_of_day(start)
    end_dt = _end_of_day(end)
    qs = FootballFixture.objects.select_related("home_team", "away_team").filter(
        kickoff_at__gte=start_dt, kickoff_at__lte=end_dt
    )
    if mine:
        team_ids = _owned_ids(user, "football")
        qs = qs.filter(home_team_id__in=team_ids) | qs.filter(away_team_id__in=team_ids)
        qs = qs.distinct()
    rows = []
    for fixture in qs[:LIMIT_PER_SOURCE]:
        title = f"{fixture.home_team.name} vs {fixture.away_team.name}"
        rows.append(_row("football", fixture.id, title, fixture.home_team.logo_url, "match", moment=fixture.kickoff_at))
    return rows


SOURCES = {
    "movie": movie_source,
    "game": game_source,
    "tv": tv_source,
    "anime": anime_source,
    "football": football_source,
}


def _start_of_day(date):
    return timezone.make_aware(datetime.combine(date, time.min), dt_timezone.utc)


def _end_of_day(date):
    return timezone.make_aware(datetime.combine(date, time.max), dt_timezone.utc)


def build_calendar(start, end, user, type_filter=None, mine=False):
    """Collect rows from the relevant sources, sorted by moment/date ascending."""
    sources = [SOURCES[type_filter]] if type_filter else SOURCES.values()
    rows = []
    for source in sources:
        rows.extend(source(start, end, user, mine))
    rows.sort(key=_sort_key)
    return rows


def _sort_key(row):
    if row["datetime"] is not None:
        return timezone.localtime(row["datetime"], dt_timezone.utc)
    return _start_of_day(row["date"])
