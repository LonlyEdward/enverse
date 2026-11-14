"""Celery task that syncs movies from TMDB into the local database.

Follows the sync rules in docs/BUILD_PLAN.md section 4: the API is only read here
(never while serving a request), upserts are idempotent, and nothing raised by a
single item aborts the run.
"""

import logging

from celery import shared_task
from django.db.models import F
from django.utils import timezone

from core.models import SyncLog
from core.sync import SyncRun, replace_trending_ranks, store_item
from core.tmdb import build_tmdb_client

from .mappers import map_detail_movie, map_list_movie
from .models import Movie

logger = logging.getLogger(__name__)

NOW_PLAYING_PAGES = 2
UPCOMING_PAGES = 2
DETAIL_BATCH = 40  # cap expensive per-movie detail calls per run


def _upsert_list_item(item, genre_map, client, run):
    """Upsert one movie from a list/trending result, recording success or error."""
    try:
        external_id, defaults = map_list_movie(item, genre_map, client)
        if external_id is None:
            run.error("movie result had no id")
            return
        existing = Movie.objects.filter(external_id=str(external_id)).first()
        new_date = defaults.get("release_date")
        # Record a release-date shift so Phase 10 can notify about it.
        if existing and existing.release_date and new_date and existing.release_date != new_date:
            defaults["previous_release_date"] = existing.release_date
        store_item(Movie, external_id, defaults)
        run.processed(1)
    except Exception as exc:  # one bad item must not abort the batch
        run.error(f"movie {item.get('id')}: {exc}")


def _sync_details(client, run):
    """Fetch rich detail for a capped batch, oldest/never-synced first."""
    batch = list(
        Movie.objects.order_by(F("details_synced_at").asc(nulls_first=True))[:DETAIL_BATCH]
    )
    for movie in batch:
        try:
            detail = client.movie_detail(movie.external_id)
            fields = map_detail_movie(detail, client)
            fields["details_synced_at"] = timezone.now()
            for name, value in fields.items():
                setattr(movie, name, value)
            movie.save(update_fields=list(fields.keys()))
        except Exception as exc:
            run.error(f"movie detail {movie.external_id}: {exc}")


@shared_task(name="movies.tasks.sync_movies")
def sync_movies():
    client = build_tmdb_client()
    if not client.is_configured:
        logger.warning("TMDB_API_KEY is not set; skipping movie sync.")
        return

    with SyncRun(SyncLog.Source.TMDB) as run:
        genre_map = client.genre_list()

        for fetch, pages in ((client.now_playing, NOW_PLAYING_PAGES), (client.upcoming, UPCOMING_PAGES)):
            for page in range(1, pages + 1):
                for item in fetch(page).get("results", []):
                    _upsert_list_item(item, genre_map, client, run)

        trending_ids = []
        for item in client.trending_movies().get("results", []):
            _upsert_list_item(item, genre_map, client, run)
            if item.get("id") is not None:
                trending_ids.append(str(item["id"]))
        replace_trending_ranks(Movie, trending_ids)

        _sync_details(client, run)
