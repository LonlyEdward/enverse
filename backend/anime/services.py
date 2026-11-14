"""Episode bookkeeping for anime.

The goal is to never flood a user with notifications for episodes that aired
before we knew about the show (see docs/BUILD_PLAN.md Phase 5). The rule we apply:

- Episodes below the next airing episode are backfilled as ``notified=True`` with
  ``aired_at=None`` — they are history, not news, and the list endpoint does not
  give us their exact air dates anyway.
- The single *scheduled* next episode is stored ``notified=False`` with its real
  ``aired_at``. When it airs, the Phase 10 detector emits it exactly once (it only
  ever emits episodes that have a known ``aired_at`` in the past), then advances.

This deliberately does not retroactively notify episodes that aired while the
worker was down; the scheduled-next mechanism covers the normal weekly cadence.
"""

from .models import AnimeEpisode


def current_season(today):
    """Return AniList ``(season, year)`` for a given date.

    December belongs to the following year's WINTER season, matching AniList's
    convention. ``today`` is passed in so nothing is frozen at import time.
    """
    month = today.month
    if month in (12, 1, 2):
        return "WINTER", today.year + 1 if month == 12 else today.year
    if month in (3, 4, 5):
        return "SPRING", today.year
    if month in (6, 7, 8):
        return "SUMMER", today.year
    return "FALL", today.year


def sync_episodes(anime, next_episode_number, next_airing_at):
    existing = set(anime.episodes.values_list("episode_number", flat=True))

    if next_episode_number:
        last_aired = next_episode_number - 1
    else:
        # No scheduled episode (finished/cancelled): everything up to the total aired.
        last_aired = anime.episodes_total or 0

    backlog = [
        AnimeEpisode(anime=anime, episode_number=number, aired_at=None, notified=True)
        for number in range(1, last_aired + 1)
        if number not in existing
    ]
    if backlog:
        AnimeEpisode.objects.bulk_create(backlog, ignore_conflicts=True)

    if next_episode_number and next_airing_at:
        AnimeEpisode.objects.update_or_create(
            anime=anime,
            episode_number=next_episode_number,
            defaults={"aired_at": next_airing_at, "notified": False},
        )
