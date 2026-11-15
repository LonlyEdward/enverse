"""Pure recommendation scoring. No database, no network — just data in, scores out.

The service layer (``services.py``) pulls candidates and the user's signals from the
DB and hands them here; everything in this module is deterministic and unit-tested
with ``SimpleTestCase``.

Scoring, per candidate of type ``T``:

    score = genre_score + QUALITY_FACTOR * rating_norm + POPULARITY_FACTOR * pop_pct

``genre_score`` sums, over the candidate's genres, an *effective* weight that blends
the user's signal for that genre within type ``T`` with a discounted share of the
same genre's signal in other types (``CROSS_TYPE_FACTOR``). A genre's signal comes
from explicit picks (``EXPLICIT_WEIGHT``) and library membership
(``LIBRARY_WEIGHTS``). ``rating_norm`` and ``pop_pct`` are both 0..1, and quality is
weighted above popularity on purpose.
"""

from collections import defaultdict
from dataclasses import dataclass, field

# Pool sizing (used by the service, kept here so all tuning lives in one place).
POOL_SIZE = 300        # top candidates per type by popularity
PER_TYPE_LIMIT = 20    # recommendations stored per type

# Genre signal weights.
EXPLICIT_WEIGHT = 4.0                                      # a genre the user explicitly picked
LIBRARY_WEIGHTS = {"favorite": 3.0, "following": 2.0, "watchlist": 1.0}
CROSS_TYPE_FACTOR = 0.5                                    # a genre liked in one type counts half elsewhere

# Non-genre adjustments. Quality intentionally outweighs raw popularity.
QUALITY_FACTOR = 0.3
POPULARITY_FACTOR = 0.2


@dataclass(frozen=True)
class Candidate:
    content_type: str
    object_id: int
    genres: tuple = ()
    rating_norm: float | None = None   # 0..1 (rating divided by the type's scale)
    popularity: float | None = None


@dataclass
class Signal:
    """A user's taste inputs. ``explicit`` is (content_type, genre) pairs; ``library``
    is (kind, content_type, genres) rows, kind being favorite/following/watchlist."""

    explicit: list = field(default_factory=list)
    library: list = field(default_factory=list)

    @property
    def is_empty(self):
        return not self.explicit and not self.library


def build_profile(signal):
    """Raw genre weight per ``(content_type, genre)`` from explicit picks + library."""
    profile = defaultdict(float)
    for content_type, genre in signal.explicit:
        profile[(content_type, genre)] += EXPLICIT_WEIGHT
    for kind, content_type, genres in signal.library:
        weight = LIBRARY_WEIGHTS.get(kind, 0.0)
        for genre in genres or ():
            profile[(content_type, genre)] += weight
    return dict(profile)


def _genre_totals(profile):
    totals = defaultdict(float)
    for (content_type, genre), weight in profile.items():
        totals[genre] += weight
    return totals


def _effective_weight(content_type, genre, profile, totals):
    here = profile.get((content_type, genre), 0.0)
    # same genre in other types, discounted
    elsewhere = totals.get(genre, 0.0) - here
    return here + CROSS_TYPE_FACTOR * elsewhere


def _percentile_map(values):
    """Map each distinct popularity value to its percentile rank (0..1) in the pool."""
    cleaned = sorted(v for v in values)
    n = len(cleaned)
    if n <= 1:
        return {v: 0.0 for v in values}
    ranks = {}
    for index, value in enumerate(cleaned):
        # fraction of the pool strictly below this value's position
        ranks[value] = index / (n - 1)
    return ranks


def rank(candidates, signal):
    """Score and sort candidates best-first, returning ``[(candidate, score, reason)]``.

    A stable tiebreak on popularity then id keeps the order deterministic.
    """
    profile = build_profile(signal)
    totals = _genre_totals(profile)
    percentiles = _percentile_map([c.popularity or 0.0 for c in candidates])

    scored = []
    for candidate in candidates:
        genre_score = 0.0
        best_weight, best_genre = 0.0, None
        for genre in candidate.genres:
            weight = _effective_weight(candidate.content_type, genre, profile, totals)
            genre_score += weight
            if weight > best_weight:
                best_weight, best_genre = weight, genre

        quality = (candidate.rating_norm or 0.0) * QUALITY_FACTOR
        popularity = percentiles.get(candidate.popularity or 0.0, 0.0) * POPULARITY_FACTOR
        score = genre_score + quality + popularity

        reason = f"Because you like {best_genre}" if best_genre else "Popular right now"
        scored.append((candidate, score, reason))

    scored.sort(key=lambda row: (-row[1], -(row[0].popularity or 0.0), row[0].object_id))
    return scored
