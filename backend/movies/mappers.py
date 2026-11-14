"""Pure functions turning TMDB JSON into Movie field dicts.

No database, no network: these take already-fetched dicts (plus a client only for
its string-only image-URL helpers) and return plain values, so they are fully
unit-testable and defensive against missing or malformed fields.
"""

from core.sync import parse_date

CAST_LIMIT = 10


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


def map_list_movie(item, genre_map, client):
    """Map one list/trending result to ``(external_id, defaults)``.

    ``external_id`` is ``None`` if the item has no id (caller skips it). Genre ids
    are resolved to names via ``genre_map``; unknown ids are dropped.
    """
    external_id = item.get("id")
    if external_id is None:
        return None, {}
    genres = [genre_map[gid] for gid in (item.get("genre_ids") or []) if gid in genre_map]
    defaults = {
        "title": (item.get("title") or item.get("name") or "").strip() or "Untitled",
        "description": item.get("overview") or "",
        "poster_url": client.poster_url(item.get("poster_path")),
        "genres": genres,
        "release_date": parse_date(item.get("release_date")),
        "rating": _float_or_none(item.get("vote_average")),
        "popularity": _float_or_none(item.get("popularity")),
    }
    return external_id, defaults


def _pick_trailer_key(videos):
    """Prefer an official YouTube 'Trailer', then any YouTube trailer, then any
    YouTube video. Return the video key or ''."""
    youtube = [v for v in videos if v.get("site") == "YouTube" and v.get("key")]
    trailers = [v for v in youtube if v.get("type") == "Trailer"]
    official = [v for v in trailers if v.get("official")]
    for group in (official, trailers, youtube):
        if group:
            return group[0].get("key", "")
    return ""


def _map_cast(cast, client):
    ordered = sorted(cast, key=lambda c: c.get("order", 10**9))[:CAST_LIMIT]
    return [
        {
            "name": c.get("name", ""),
            "character": c.get("character", ""),
            "profile_url": client.profile_url(c.get("profile_path")),
        }
        for c in ordered
        if c.get("name")
    ]


def _map_companies(companies, client):
    return [
        {"name": c.get("name", ""), "logo_url": client.profile_url(c.get("logo_path"))}
        for c in companies
        if c.get("name")
    ]


def map_detail_movie(detail, client):
    """Map a /movie/{id}?append_to_response=videos,credits payload to the detail
    fields. Genres from the detail response are authoritative (full objects)."""
    genres = [g["name"] for g in (detail.get("genres") or []) if g.get("name")]
    videos = (detail.get("videos") or {}).get("results") or []
    cast = (detail.get("credits") or {}).get("cast") or []
    companies = detail.get("production_companies") or []
    return {
        "description": detail.get("overview") or "",
        "genres": genres,
        "backdrop_url": client.backdrop_url(detail.get("backdrop_path")),
        "runtime": _int_or_none(detail.get("runtime")),
        "trailer_youtube_key": _pick_trailer_key(videos),
        "cast": _map_cast(cast, client),
        "production_companies": _map_companies(companies, client),
    }
