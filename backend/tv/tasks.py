"""Celery task that syncs TV shows (and their seasons) from TMDB."""

import logging

from celery import shared_task
from django.db.models import F
from django.utils import timezone

from core.models import SyncLog
from core.sync import SyncRun, replace_trending_ranks, store_item
from core.tmdb import build_tmdb_client

from .mappers import map_detail_tv, map_list_tv
from .models import TVSeason, TVShow, season_state

logger = logging.getLogger(__name__)

ON_THE_AIR_PAGES = 2
POPULAR_PAGES = 2
DETAIL_BATCH = 40


def _upsert_list_item(item, genre_map, client, run):
    try:
        external_id, defaults = map_list_tv(item, genre_map, client)
        if external_id is None:
            run.error("tv result had no id")
            return
        store_item(TVShow, external_id, defaults)
        run.processed(1)
    except Exception as exc:
        run.error(f"tv {item.get('id')}: {exc}")


def _upsert_seasons(show, seasons):
    """Replace-in-place the show's seasons, computing each season's state."""
    today = timezone.localdate()
    for season in seasons:
        TVSeason.objects.update_or_create(
            show=show,
            season_number=season["season_number"],
            defaults={
                "air_date": season["air_date"],
                "state": season_state(season["air_date"], season["season_number"], show.next_episode_season, today),
            },
        )


def _sync_details(client, run):
    batch = list(TVShow.objects.order_by(F("details_synced_at").asc(nulls_first=True))[:DETAIL_BATCH])
    for show in batch:
        try:
            detail = client.tv_detail(show.external_id)
            show_fields, seasons = map_detail_tv(detail, client)
            show_fields["details_synced_at"] = timezone.now()
            for name, value in show_fields.items():
                setattr(show, name, value)
            show.save(update_fields=list(show_fields.keys()))
            _upsert_seasons(show, seasons)
        except Exception as exc:
            run.error(f"tv detail {show.external_id}: {exc}")


@shared_task(name="tv.tasks.sync_tv")
def sync_tv():
    client = build_tmdb_client()
    if not client.is_configured:
        logger.warning("TMDB_API_KEY is not set; skipping TV sync.")
        return

    with SyncRun(SyncLog.Source.TMDB) as run:
        genre_map = client.tv_genre_list()

        for fetch, pages in ((client.on_the_air, ON_THE_AIR_PAGES), (client.popular_tv, POPULAR_PAGES)):
            for page in range(1, pages + 1):
                for item in fetch(page).get("results", []):
                    _upsert_list_item(item, genre_map, client, run)

        trending_ids = []
        for item in client.trending_tv().get("results", []):
            _upsert_list_item(item, genre_map, client, run)
            if item.get("id") is not None:
                trending_ids.append(str(item["id"]))
        replace_trending_ranks(TVShow, trending_ids)

        _sync_details(client, run)
