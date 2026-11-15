"""Glue between the DB and the pure engine: gather signals, score, store.

Recommendations cover the four ``SyncedContent`` types only (football teams have no
genres or popularity to rank on). Ratings use different scales per source, so each
is normalised to 0..1 before scoring.
"""

import logging
from collections import defaultdict

from django.db.models import F
from django.db import transaction

from accounts.models import GenrePreference
from core.registry import CONTENT_TYPES, get_content_model
from library.models import Bookmark, Favorite, Following, WatchlistItem

from . import engine
from .models import Recommendation

logger = logging.getLogger(__name__)

# Source rating scales, normalised to 0..1 for the quality term.
RATING_SCALE = {"movie": 10.0, "tv": 10.0, "anime": 10.0, "game": 5.0}

# Library kinds that feed taste (bookmark is a "read later" marker, not a taste
# signal, so it is excluded here — but it still excludes an item as a candidate).
_TASTE_KINDS = (("favorite", Favorite), ("following", Following), ("watchlist", WatchlistItem))
_ALL_KINDS = _TASTE_KINDS + (("bookmark", Bookmark),)


def _library_pairs(user, models):
    pairs = set()
    for _, model in models:
        pairs.update(model.objects.filter(user=user).values_list("content_type", "object_id"))
    return pairs


def _user_signal(user):
    explicit = list(GenrePreference.objects.filter(user=user).values_list("content_type", "genre"))

    # Genres of the user's taste-bearing library items (one query per content type).
    want = defaultdict(list)  # content_type -> [(kind, object_id)]
    for kind, model in _TASTE_KINDS:
        for content_type, object_id in model.objects.filter(user=user).values_list("content_type", "object_id"):
            want[content_type].append((kind, object_id))

    library = []
    for content_type, entries in want.items():
        if content_type not in CONTENT_TYPES:  # football teams carry no genres
            continue
        model = get_content_model(content_type)
        genres_by_id = dict(model.objects.filter(id__in=[oid for _, oid in entries]).values_list("id", "genres"))
        for kind, object_id in entries:
            library.append((kind, content_type, genres_by_id.get(object_id) or []))

    return engine.Signal(explicit=explicit, library=library)


def _candidates(exclude_pairs):
    candidates = []
    for content_type in CONTENT_TYPES:
        model = get_content_model(content_type)
        scale = RATING_SCALE[content_type]
        pool = model.objects.order_by(F("popularity").desc(nulls_last=True))[: engine.POOL_SIZE]
        for obj in pool.only("id", "genres", "rating", "popularity"):
            if (content_type, obj.id) in exclude_pairs:
                continue
            rating = getattr(obj, "rating", None)
            rating_norm = min(rating / scale, 1.0) if rating is not None else None
            candidates.append(
                engine.Candidate(
                    content_type=content_type,
                    object_id=obj.id,
                    genres=tuple(obj.genres or ()),
                    rating_norm=rating_norm,
                    popularity=obj.popularity,
                )
            )
    return candidates


def recompute_for_user(user):
    """Rebuild one user's recommendations. Returns how many were stored."""
    signal = _user_signal(user)
    candidates = _candidates(_library_pairs(user, _ALL_KINDS))
    ranked = engine.rank(candidates, signal)

    per_type = defaultdict(int)
    rows = []
    for candidate, score, reason in ranked:
        if per_type[candidate.content_type] >= engine.PER_TYPE_LIMIT:
            continue
        per_type[candidate.content_type] += 1
        rows.append(
            Recommendation(
                user=user,
                content_type=candidate.content_type,
                object_id=candidate.object_id,
                score=score,
                reason=reason,
            )
        )

    with transaction.atomic():
        Recommendation.objects.filter(user=user).delete()
        Recommendation.objects.bulk_create(rows)
    return len(rows)
