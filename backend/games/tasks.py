"""Celery task that syncs games from RAWG."""

import logging
from datetime import timedelta

from celery import shared_task
from django.db.models import F
from django.utils import timezone

from core.models import SyncLog
from core.rawg import build_rawg_client
from core.sync import SyncRun, replace_trending_ranks, store_item

from .mappers import extract_screenshots, extract_trailer, map_game_detail, map_list_game
from .models import Game

logger = logging.getLogger(__name__)

UPCOMING_DAYS = 180
RECENT_DAYS = 60
DETAIL_BATCH = 20  # small: the free RAWG quota is limited and detail is 3 calls each
TRENDING_LIMIT = 40


def _upsert_list_item(item, run):
    try:
        external_id, defaults = map_list_game(item)
        if external_id is None:
            run.error("game result had no id")
            return
        existing = Game.objects.filter(external_id=str(external_id)).first()
        new_date = defaults.get("release_date")
        if existing and existing.release_date and new_date and existing.release_date != new_date:
            defaults["previous_release_date"] = existing.release_date
        store_item(Game, external_id, defaults)
        run.processed(1)
    except Exception as exc:
        run.error(f"game {item.get('id')}: {exc}")


def _sync_details(client, run):
    batch = list(Game.objects.order_by(F("details_synced_at").asc(nulls_first=True))[:DETAIL_BATCH])
    for game in batch:
        try:
            fields = map_game_detail(client.game_detail(game.external_id))
            fields["screenshots"] = extract_screenshots(client.game_screenshots(game.external_id))
            fields["trailer_url"] = extract_trailer(client.game_movies(game.external_id))
            fields["details_synced_at"] = timezone.now()
            for name, value in fields.items():
                setattr(game, name, value)
            game.save(update_fields=list(fields.keys()))
        except Exception as exc:
            run.error(f"game detail {game.external_id}: {exc}")


@shared_task(name="games.tasks.sync_games")
def sync_games():
    client = build_rawg_client()
    if not client.is_configured:
        logger.warning("RAWG_API_KEY is not set; skipping games sync.")
        return

    with SyncRun(SyncLog.Source.RAWG) as run:
        today = timezone.localdate()
        upcoming = client.list_games(dates=(today, today + timedelta(days=UPCOMING_DAYS)), ordering="released")
        recent = client.list_games(dates=(today - timedelta(days=RECENT_DAYS), today), ordering="-released")
        for payload in (upcoming, recent):
            for item in payload.get("results", []):
                _upsert_list_item(item, run)

        # RAWG has no trending endpoint; "most added recently" is a good stand-in.
        trending = client.list_games(
            dates=(today - timedelta(days=RECENT_DAYS), today + timedelta(days=UPCOMING_DAYS)), ordering="-added"
        )
        trending_ids = []
        for item in trending.get("results", []):
            _upsert_list_item(item, run)
            if item.get("id") is not None:
                trending_ids.append(str(item["id"]))
        replace_trending_ranks(Game, trending_ids[:TRENDING_LIMIT])

        _sync_details(client, run)
