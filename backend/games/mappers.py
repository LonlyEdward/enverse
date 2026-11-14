"""Pure functions turning RAWG JSON into Game field dicts."""

from core.sync import parse_date

SCREENSHOT_LIMIT = 10


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


def map_list_game(item):
    """Map one RAWG /games result to ``(external_id, defaults)``."""
    external_id = item.get("id")
    if external_id is None:
        return None, {}
    genres = [g["name"] for g in (item.get("genres") or []) if g.get("name")]
    platforms = [
        p["platform"]["name"]
        for p in (item.get("platforms") or [])
        if p.get("platform") and p["platform"].get("name")
    ]
    defaults = {
        "title": (item.get("name") or "").strip() or "Untitled",
        "poster_url": item.get("background_image") or "",
        "genres": genres,
        "platforms": platforms,
        "release_date": parse_date(item.get("released")),
        "rating": _float_or_none(item.get("rating")),  # RAWG 0-5
        "metacritic": _int_or_none(item.get("metacritic")),
        "popularity": _float_or_none(item.get("added")),  # how many users added it
    }
    return external_id, defaults


def map_game_detail(detail):
    developers = [d["name"] for d in (detail.get("developers") or []) if d.get("name")]
    return {
        "description": detail.get("description_raw") or "",
        "developers": developers,
        "metacritic": _int_or_none(detail.get("metacritic")),
    }


def extract_screenshots(payload):
    return [s["image"] for s in (payload.get("results") or []) if s.get("image")][:SCREENSHOT_LIMIT]


def extract_trailer(payload):
    """Pick the first trailer's best available MP4 from /games/{id}/movies."""
    for movie in payload.get("results") or []:
        data = movie.get("data") or {}
        url = data.get("max") or data.get("480")
        if url:
            return url
    return ""
