"""Pure functions turning API-Football JSON into field dicts.

Nothing here touches the database or the network, so every mapper is unit-tested
on its own. Each one defaults missing fields rather than trusting the payload: a
shape surprise degrades a single fixture, it never aborts the sync.
"""

from django.utils.dateparse import parse_datetime

from .services import map_status


def map_team(team):
    """Map one ``teams.home``/``teams.away`` object to ``(external_id, defaults)``.

    Returns ``(None, {})`` when the team carries no id, so the caller can skip it.
    ``competition`` is intentionally left to the task, which knows which league is
    being synced (the embedded fixture team object does not name it).
    """
    external_id = team.get("id")
    if external_id is None:
        return None, {}
    defaults = {
        "name": (team.get("name") or "").strip() or "Unknown",
        "logo_url": team.get("logo") or "",
    }
    return external_id, defaults


def map_fixture(item):
    """Map one API-Football ``/fixtures`` row to the pieces a sync needs.

    Returns ``None`` when an essential id (fixture, either team) or the kickoff
    time is missing or unparseable — those cannot be stored, so the fixture is
    skipped rather than forced in with bad data.
    """
    fixture = item.get("fixture") or {}
    league = item.get("league") or {}
    teams = item.get("teams") or {}
    goals = item.get("goals") or {}
    home = teams.get("home") or {}
    away = teams.get("away") or {}

    external_id = fixture.get("id")
    home_id = home.get("id")
    away_id = away.get("id")
    kickoff_at = parse_datetime(fixture.get("date") or "")
    if external_id is None or home_id is None or away_id is None or kickoff_at is None:
        return None

    status_short = (fixture.get("status") or {}).get("short")
    venue = (fixture.get("venue") or {}).get("name") or ""
    league_id = league.get("id")
    return {
        "external_id": external_id,
        "home": map_team(home),
        "away": map_team(away),
        "league_external_id": league_id if isinstance(league_id, int) else None,
        "competition": (league.get("name") or "").strip(),
        "round": (league.get("round") or "").strip(),
        "venue": venue.strip(),
        "kickoff_at": kickoff_at,
        "status": map_status(status_short),
        "home_score": goals.get("home"),
        "away_score": goals.get("away"),
    }
