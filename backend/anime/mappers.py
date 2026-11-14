"""Pure functions turning AniList media nodes into Anime field dicts."""

from datetime import datetime, timezone as dt_timezone

from .models import Anime

_STATUS_MAP = {
    "RELEASING": Anime.AiringStatus.RELEASING,
    "FINISHED": Anime.AiringStatus.FINISHED,
    "NOT_YET_RELEASED": Anime.AiringStatus.NOT_YET_RELEASED,
    "CANCELLED": Anime.AiringStatus.CANCELLED,
    "HIATUS": Anime.AiringStatus.HIATUS,
}

_SEASON_MAP = {
    "WINTER": Anime.Season.WINTER,
    "SPRING": Anime.Season.SPRING,
    "SUMMER": Anime.Season.SUMMER,
    "FALL": Anime.Season.FALL,
}


def map_airing_status(value):
    return _STATUS_MAP.get(value, Anime.AiringStatus.NOT_YET_RELEASED)


def map_season(value):
    return _SEASON_MAP.get(value, "")


def _timestamp_to_dt(timestamp):
    """AniList airingAt is a Unix timestamp (seconds). Return an aware UTC datetime."""
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=dt_timezone.utc)


def _score_to_rating(score):
    # AniList averageScore is 0-100; our rating is 0-10.
    try:
        return round(score / 10, 1) if score is not None else None
    except (TypeError, ValueError):
        return None


def _float_or_none(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def map_media(node):
    """Map one AniList media node to ``(external_id, defaults, next_episode)``.

    ``next_episode`` is ``{number, airing_at}`` (or Nones), passed to the episode
    sync. ``external_id`` is None when the node has no id.
    """
    external_id = node.get("id")
    if external_id is None:
        return None, {}, {"number": None, "airing_at": None}

    title = node.get("title") or {}
    name = title.get("english") or title.get("romaji") or title.get("native") or "Untitled"
    next_ep = node.get("nextAiringEpisode") or {}
    airing_at = _timestamp_to_dt(next_ep.get("airingAt"))
    studios = [s["name"] for s in ((node.get("studios") or {}).get("nodes") or []) if s.get("name")]

    defaults = {
        "title": name,
        "description": node.get("description") or "",
        "poster_url": (node.get("coverImage") or {}).get("large") or "",
        "banner_url": node.get("bannerImage") or "",
        "genres": node.get("genres") or [],
        "rating": _score_to_rating(node.get("averageScore")),
        "popularity": _float_or_none(node.get("popularity")),
        "airing_status": map_airing_status(node.get("status")),
        "season": map_season(node.get("season")),
        "season_year": node.get("seasonYear"),
        "episodes_total": node.get("episodes"),
        "studios": studios,
        "next_airing_episode_number": next_ep.get("episode"),
        "next_airing_at": airing_at,
    }
    return external_id, defaults, {"number": next_ep.get("episode"), "airing_at": airing_at}
