"""One registry mapping each content type to its model and a summary shape.

Library, search, notifications, recommendations and the calendar all deal with a
mix of content types. Routing that through a single registry means they share one
code path instead of special-casing movies vs. games vs. anime everywhere.

Football is intentionally absent: it is fixtures and teams, not ``SyncedContent``
items, and is handled by its own code (Phase 7). Content types are registered
here as their phases land.
"""

from collections import defaultdict

from django.apps import apps

# content_type string -> (app_label, model_name). Keep in sync with
# core.choices.ContentType. Football is handled separately (see module docstring).
CONTENT_MODELS = {
    "movie": ("movies", "Movie"),
    "tv": ("tv", "TVShow"),
    "anime": ("anime", "Anime"),
    "game": ("games", "Game"),
}

CONTENT_TYPES = tuple(CONTENT_MODELS)

# Reverse lookup (app_label, model_name_lower) -> content_type, for summarize().
_MODEL_TO_TYPE = {
    (app_label, model_name.lower()): content_type
    for content_type, (app_label, model_name) in CONTENT_MODELS.items()
}


def get_content_model(content_type):
    """Return the Django model class for a content type, or raise ``ValueError``."""
    try:
        app_label, model_name = CONTENT_MODELS[content_type]
    except KeyError:
        raise ValueError(f"Unknown content type: {content_type!r}")
    return apps.get_model(app_label, model_name)


def content_type_of(obj):
    """Return the content type string for a model instance, or raise ``ValueError``."""
    key = (obj._meta.app_label, obj._meta.model_name)
    try:
        return _MODEL_TO_TYPE[key]
    except KeyError:
        raise ValueError(f"{obj._meta.label} is not a registered content type")


def load_content(pairs):
    """Resolve ``[(content_type, object_id), ...]`` to a dict of model instances.

    Returns ``{(content_type, object_id): obj}`` and does **one query per content
    type** (not one per pair), so callers that mix types stay free of N+1 queries.
    Ids with no matching row are simply absent from the result.
    """
    ids_by_type = defaultdict(set)
    for content_type, object_id in pairs:
        ids_by_type[content_type].add(object_id)

    resolved = {}
    for content_type, ids in ids_by_type.items():
        model = get_content_model(content_type)
        for obj in model.objects.filter(id__in=ids):
            resolved[(content_type, obj.id)] = obj
    return resolved


def _as_date(value):
    """Coerce a date/datetime/None to a plain date (or None)."""
    if value is None:
        return None
    return value.date() if hasattr(value, "date") else value


def summarize(obj):
    """Return a small, uniform dict describing a content item for mixed lists.

    Shape: ``content_type``, ``id``, ``title``, ``poster_url``, ``date`` (the most
    relevant date for that type, or None) and a short ``subtitle``.
    """
    content_type = content_type_of(obj)
    summary = {
        "content_type": content_type,
        "id": obj.id,
        "title": obj.title,
        "poster_url": obj.poster_url,
        "date": None,
        "subtitle": "",
    }

    if content_type == "movie":
        summary["date"] = obj.release_date
        summary["subtitle"] = "Movie"
    elif content_type == "tv":
        summary["subtitle"] = obj.get_status_display()
    elif content_type == "anime":
        summary["date"] = _as_date(obj.next_airing_at)
        summary["subtitle"] = obj.get_airing_status_display()
    elif content_type == "game":
        summary["date"] = obj.release_date
        summary["subtitle"] = ", ".join(obj.platforms[:3]) if obj.platforms else "Game"

    return summary
