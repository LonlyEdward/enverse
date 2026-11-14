"""Pure functions turning TMDB TV JSON into TVShow field dicts."""

from core.sync import parse_date

from .models import TVShow

# TMDB status string -> our TVShow.Status. Anything else (In Production, Planned,
# Pilot, ...) is treated as a returning/active series.
_STATUS_MAP = {
    "Returning Series": TVShow.Status.RETURNING,
    "Ended": TVShow.Status.ENDED,
    "Canceled": TVShow.Status.CANCELED,
    "Cancelled": TVShow.Status.CANCELED,
}


def _float_or_none(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _int_or_none(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def map_tv_status(tmdb_status):
    return _STATUS_MAP.get(tmdb_status, TVShow.Status.RETURNING)


def map_list_tv(item, genre_map, client):
    """Map one TV list/trending result to ``(external_id, defaults)``."""
    external_id = item.get("id")
    if external_id is None:
        return None, {}
    genres = [genre_map[gid] for gid in (item.get("genre_ids") or []) if gid in genre_map]
    defaults = {
        "title": (item.get("name") or item.get("title") or "").strip() or "Untitled",
        "description": item.get("overview") or "",
        "poster_url": client.poster_url(item.get("poster_path")),
        "genres": genres,
        "first_air_date": parse_date(item.get("first_air_date")),
        "rating": _float_or_none(item.get("vote_average")),
        "popularity": _float_or_none(item.get("popularity")),
    }
    return external_id, defaults


def _pick_trailer_key(videos):
    youtube = [v for v in videos if v.get("site") == "YouTube" and v.get("key")]
    trailers = [v for v in youtube if v.get("type") == "Trailer"]
    official = [v for v in trailers if v.get("official")]
    for group in (official, trailers, youtube):
        if group:
            return group[0].get("key", "")
    return ""


def map_detail_tv(detail, client):
    """Map a /tv/{id} payload to the show's detail fields and its season list.

    Returns ``(show_fields, seasons)`` where ``seasons`` is a list of
    ``{season_number, air_date}`` dicts (state is computed at upsert time).
    """
    genres = [g["name"] for g in (detail.get("genres") or []) if g.get("name")]
    videos = (detail.get("videos") or {}).get("results") or []
    next_episode = detail.get("next_episode_to_air") or {}

    show_fields = {
        "description": detail.get("overview") or "",
        "genres": genres,
        "status": map_tv_status(detail.get("status")),
        "number_of_seasons": _int_or_none(detail.get("number_of_seasons")),
        "backdrop_url": client.backdrop_url(detail.get("backdrop_path")),
        "trailer_youtube_key": _pick_trailer_key(videos),
        "next_episode_air_date": parse_date(next_episode.get("air_date")),
        "next_episode_season": _int_or_none(next_episode.get("season_number")),
        "next_episode_number": _int_or_none(next_episode.get("episode_number")),
    }

    seasons = []
    for season in detail.get("seasons") or []:
        number = _int_or_none(season.get("season_number"))
        if number is None:
            continue
        seasons.append({"season_number": number, "air_date": parse_date(season.get("air_date"))})

    return show_fields, seasons
