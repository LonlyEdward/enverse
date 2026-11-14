"""Celery task that syncs anime (and their episodes) from AniList."""

import logging

from celery import shared_task
from django.utils import timezone

from core.anilist import build_anilist_client
from core.models import SyncLog
from core.sync import SyncRun, replace_trending_ranks, store_item

from .mappers import map_media
from .models import Anime
from .services import current_season, sync_episodes

logger = logging.getLogger(__name__)

PER_PAGE = 50


def _upsert(node, run):
    try:
        external_id, defaults, next_ep = map_media(node)
        if external_id is None:
            run.error("anime node had no id")
            return
        anime, _ = store_item(Anime, external_id, defaults)
        sync_episodes(anime, next_ep["number"], next_ep["airing_at"])
        run.processed(1)
    except Exception as exc:
        run.error(f"anime {node.get('id')}: {exc}")


@shared_task(name="anime.tasks.sync_anime")
def sync_anime():
    # AniList needs no key, so this always runs.
    client = build_anilist_client()
    with SyncRun(SyncLog.Source.ANILIST) as run:
        season, year = current_season(timezone.localdate())

        # Currently releasing, and the current season's not-yet-released shows.
        for params in (
            {"status": "RELEASING", "sort": ["POPULARITY_DESC"]},
            {"season": season, "season_year": year, "status": "NOT_YET_RELEASED", "sort": ["POPULARITY_DESC"]},
        ):
            for node in client.fetch_media_page(per_page=PER_PAGE, **params):
                _upsert(node, run)

        trending_ids = []
        for node in client.fetch_media_page(sort=["TRENDING_DESC"], per_page=PER_PAGE):
            _upsert(node, run)
            if node.get("id") is not None:
                trending_ids.append(str(node["id"]))
        replace_trending_ranks(Anime, trending_ids)
