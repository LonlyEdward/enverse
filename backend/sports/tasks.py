"""Celery task that syncs football fixtures and teams from API-Football.

Request budget: one ``/fixtures`` call per league (teams are read from the
fixtures payload, so no separate ``/teams`` calls). Six leagues => 6 requests per
run; beat runs every 3 hours => 8 runs/day => ~48 requests/day, which fits the
free plan's 100/day allowance with headroom. If the plan rejects a season, that
league's call raises and is recorded as a per-item error (partial/failed
SyncLog), while the other leagues still sync.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from core.apifootball import build_apifootball_client
from core.models import SyncLog
from core.sync import SyncRun

from .mappers import map_fixture
from .models import FootballFixture, FootballTeam
from .services import current_season

logger = logging.getLogger(__name__)

# API-Football league ids. The Champions League (2) is listed first on purpose:
# a team's single ``competition`` field is set from the league being synced, and
# processing the domestic leagues after UCL means a club that plays in both ends
# up labelled with its domestic league (the more useful default) rather than UCL.
LEAGUES = [2, 39, 140, 135, 78, 61]
LEAGUE_NAMES = {
    2: "UEFA Champions League",
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
}

DAYS_BACK = 2
DAYS_AHEAD = 28


def _upsert_team(mapped_team, competition, cache):
    """Upsert one team (cached per run) and return it, or None if it has no id."""
    external_id, defaults = mapped_team
    if external_id is None:
        return None
    key = str(external_id)
    if key in cache:
        return cache[key]
    team, _ = FootballTeam.objects.update_or_create(
        external_id=key, defaults={**defaults, "competition": competition}
    )
    cache[key] = team
    return team


def _upsert_fixture(item, competition, run, team_cache):
    try:
        mapped = map_fixture(item)
        if mapped is None:
            run.error(f"fixture {(item.get('fixture') or {}).get('id')}: missing id/teams/kickoff")
            return
        home = _upsert_team(mapped["home"], competition, team_cache)
        away = _upsert_team(mapped["away"], competition, team_cache)
        if home is None or away is None or home.pk == away.pk:
            run.error(f"fixture {mapped['external_id']}: bad teams")
            return
        FootballFixture.objects.update_or_create(
            external_id=str(mapped["external_id"]),
            defaults={
                "home_team": home,
                "away_team": away,
                "competition": mapped["competition"] or competition,
                "league_external_id": mapped["league_external_id"],
                "round": mapped["round"],
                "venue": mapped["venue"],
                "kickoff_at": mapped["kickoff_at"],
                "status": mapped["status"],
                "home_score": mapped["home_score"],
                "away_score": mapped["away_score"],
            },
        )
        run.processed(1)
    except Exception as exc:
        run.error(f"fixture {(item.get('fixture') or {}).get('id')}: {exc}")


@shared_task(name="sports.tasks.sync_football")
def sync_football():
    client = build_apifootball_client()
    if not client.is_configured:
        logger.warning("API_FOOTBALL_KEY is not set; skipping football sync.")
        return

    with SyncRun(SyncLog.Source.API_FOOTBALL) as run:
        today = timezone.localdate()
        season = current_season(today)
        date_from = today - timedelta(days=DAYS_BACK)
        date_to = today + timedelta(days=DAYS_AHEAD)
        team_cache = {}

        for league in LEAGUES:
            competition = LEAGUE_NAMES.get(league, "")
            try:
                rows = client.fixtures(league=league, season=season, date_from=date_from, date_to=date_to)
            except Exception as exc:
                # One league (e.g. a season the free plan forbids) must not stop
                # the rest. Record it and move on.
                run.error(f"league {league} season {season}: {exc}")
                continue
            for item in rows:
                _upsert_fixture(item, competition, run, team_cache)
