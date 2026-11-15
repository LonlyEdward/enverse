"""Tests for the football sync and the public football endpoints.

No live API-Football calls: the client is faked and the 200-with-errors path is
exercised against a stub response object.
"""

from datetime import date, datetime, timedelta, timezone as dt_timezone
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from core.apifootball import APIFootballClient, APIFootballError
from core.models import SyncLog
from sports.mappers import map_fixture, map_team
from sports.models import FootballFixture, FootballTeam
from sports.services import current_season, map_status
from sports.tasks import sync_football


# --- fixtures-as-data helpers ----------------------------------------------

def api_fixture(fixture_id, home, away, *, status="NS", goals=(None, None), date_="2026-01-10T19:00:00+00:00",
                league=39, league_name="Premier League"):
    home_id, home_name = home
    away_id, away_name = away
    return {
        "fixture": {
            "id": fixture_id,
            "date": date_,
            "venue": {"id": 1, "name": "Stadium", "city": "City"},
            "status": {"long": "x", "short": status, "elapsed": None},
        },
        "league": {"id": league, "name": league_name, "season": 2025, "round": "Regular Season - 1"},
        "teams": {
            "home": {"id": home_id, "name": home_name, "logo": f"https://logo/{home_id}.png"},
            "away": {"id": away_id, "name": away_name, "logo": f"https://logo/{away_id}.png"},
        },
        "goals": {"home": goals[0], "away": goals[1]},
    }


class FakeAPIFootball:
    is_configured = True

    def __init__(self, by_league=None, fail_leagues=None):
        self._by_league = by_league or {}
        self._fail = set(fail_leagues or ())

    def fixtures(self, *, league, season, date_from, date_to):
        if league in self._fail:
            raise APIFootballError(f"league {league} not allowed on plan")
        return self._by_league.get(league, [])


# --- pure logic -------------------------------------------------------------

class StatusMapTests(SimpleTestCase):
    def test_mapping_table(self):
        cases = {
            "NS": "scheduled", "TBD": "scheduled",
            "1H": "live", "HT": "live", "2H": "live", "ET": "live", "BT": "live",
            "P": "live", "LIVE": "live", "SUSP": "live", "INT": "live",
            "FT": "finished", "AET": "finished", "PEN": "finished",
            "PST": "postponed",
            "CANC": "cancelled", "ABD": "cancelled", "AWD": "cancelled", "WO": "cancelled",
        }
        for short, expected in cases.items():
            self.assertEqual(map_status(short), expected, short)

    def test_unknown_and_empty_default_to_scheduled(self):
        self.assertEqual(map_status("ZZZ"), "scheduled")
        self.assertEqual(map_status(None), "scheduled")
        self.assertEqual(map_status(""), "scheduled")

    def test_case_insensitive(self):
        self.assertEqual(map_status("ft"), "finished")


class CurrentSeasonTests(SimpleTestCase):
    def test_july_boundary(self):
        self.assertEqual(current_season(date(2026, 6, 30)), 2025)  # June -> previous season
        self.assertEqual(current_season(date(2026, 7, 1)), 2026)   # July -> current season
        self.assertEqual(current_season(date(2026, 12, 31)), 2026)
        self.assertEqual(current_season(date(2026, 1, 1)), 2025)


class MapperTests(SimpleTestCase):
    def test_map_fixture_full(self):
        mapped = map_fixture(api_fixture(100, (1, "Arsenal"), (2, "Chelsea"), status="FT", goals=(2, 1)))
        self.assertEqual(mapped["external_id"], 100)
        self.assertEqual(mapped["home"], (1, {"name": "Arsenal", "logo_url": "https://logo/1.png"}))
        self.assertEqual(mapped["away"][0], 2)
        self.assertEqual(mapped["competition"], "Premier League")
        self.assertEqual(mapped["league_external_id"], 39)
        self.assertEqual(mapped["round"], "Regular Season - 1")
        self.assertEqual(mapped["venue"], "Stadium")
        self.assertEqual(mapped["status"], "finished")
        self.assertEqual((mapped["home_score"], mapped["away_score"]), (2, 1))
        self.assertEqual(mapped["kickoff_at"], datetime(2026, 1, 10, 19, 0, tzinfo=dt_timezone.utc))

    def test_map_fixture_skips_on_missing_essentials(self):
        self.assertIsNone(map_fixture({"fixture": {"id": None}}))  # no id
        no_kickoff = api_fixture(1, (1, "A"), (2, "B"))
        no_kickoff["fixture"]["date"] = ""
        self.assertIsNone(map_fixture(no_kickoff))

    def test_map_team_defaults(self):
        self.assertEqual(map_team({}), (None, {}))
        self.assertEqual(map_team({"id": 5, "name": "  ", "logo": None}), (5, {"name": "Unknown", "logo_url": ""}))


# --- client: 200-with-errors ------------------------------------------------

class _StubResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class _StubSession:
    def __init__(self, response):
        self._response = response
        self.headers = {}

    def get(self, url, params=None, headers=None):
        return self._response


class ClientErrorsTests(SimpleTestCase):
    def test_errors_object_on_http_200_raises(self):
        session = _StubSession(_StubResponse({"errors": {"plan": "season not allowed"}, "response": []}))
        client = APIFootballClient(api_key="k", session=session)
        with self.assertRaises(APIFootballError):
            client.fixtures(league=39, season=2025, date_from=date(2026, 1, 1), date_to=date(2026, 2, 1))

    def test_empty_errors_list_is_success(self):
        session = _StubSession(_StubResponse({"errors": [], "response": [api_fixture(1, (1, "A"), (2, "B"))]}))
        client = APIFootballClient(api_key="k", session=session)
        rows = client.fixtures(league=39, season=2025, date_from=date(2026, 1, 1), date_to=date(2026, 2, 1))
        self.assertEqual(len(rows), 1)


# --- sync task --------------------------------------------------------------

class SyncFootballTests(TestCase):
    @mock.patch("sports.tasks.build_apifootball_client")
    def test_creates_teams_and_fixtures_idempotently(self, build):
        build.return_value = FakeAPIFootball(
            by_league={39: [api_fixture(100, (1, "Arsenal"), (2, "Chelsea"))]}
        )
        sync_football()
        self.assertEqual(FootballTeam.objects.count(), 2)
        self.assertEqual(FootballFixture.objects.count(), 1)
        sync_football()  # second run must not duplicate
        self.assertEqual(FootballTeam.objects.count(), 2)
        self.assertEqual(FootballFixture.objects.count(), 1)
        self.assertEqual(SyncLog.objects.latest("started_at").status, SyncLog.Status.SUCCESS)

    @mock.patch("sports.tasks.build_apifootball_client")
    def test_team_dedupe_across_fixtures(self, build):
        # The same team (id 1) appears in two fixtures; it must be stored once.
        build.return_value = FakeAPIFootball(
            by_league={
                39: [
                    api_fixture(100, (1, "Arsenal"), (2, "Chelsea")),
                    api_fixture(101, (3, "Spurs"), (1, "Arsenal")),
                ]
            }
        )
        sync_football()
        self.assertEqual(FootballTeam.objects.filter(external_id="1").count(), 1)
        self.assertEqual(FootballFixture.objects.count(), 2)

    @mock.patch("sports.tasks.build_apifootball_client")
    def test_fixture_updates_when_score_changes(self, build):
        build.return_value = FakeAPIFootball(
            by_league={39: [api_fixture(100, (1, "Arsenal"), (2, "Chelsea"), status="NS")]}
        )
        sync_football()
        build.return_value = FakeAPIFootball(
            by_league={39: [api_fixture(100, (1, "Arsenal"), (2, "Chelsea"), status="FT", goals=(3, 0))]}
        )
        sync_football()
        fixture = FootballFixture.objects.get(external_id="100")
        self.assertEqual(fixture.status, FootballFixture.Status.FINISHED)
        self.assertEqual((fixture.home_score, fixture.away_score), (3, 0))

    @mock.patch("sports.tasks.build_apifootball_client")
    def test_one_bad_league_does_not_stop_the_rest(self, build):
        build.return_value = FakeAPIFootball(
            by_league={39: [api_fixture(100, (1, "A"), (2, "B"))]}, fail_leagues={2}
        )
        sync_football()
        self.assertEqual(FootballFixture.objects.count(), 1)
        # One league errored but fixtures were processed -> partial.
        self.assertEqual(SyncLog.objects.latest("started_at").status, SyncLog.Status.PARTIAL)

    @mock.patch("sports.tasks.build_apifootball_client")
    def test_all_leagues_failing_marks_failed(self, build):
        build.return_value = FakeAPIFootball(fail_leagues={2, 39, 140, 135, 78, 61})
        sync_football()
        self.assertEqual(SyncLog.objects.latest("started_at").status, SyncLog.Status.FAILED)

    def test_missing_key_exits_cleanly(self):
        with self.settings(API_FOOTBALL_KEY=""):
            with self.assertLogs("sports.tasks", level="WARNING"):
                sync_football()
        self.assertEqual(FootballFixture.objects.count(), 0)
        self.assertEqual(SyncLog.objects.count(), 0)


# --- endpoints --------------------------------------------------------------

class FootballEndpointTests(APITestCase):
    def setUp(self):
        self.now = timezone.now()
        self.arsenal = FootballTeam.objects.create(external_id="1", name="Arsenal", competition="Premier League")
        self.chelsea = FootballTeam.objects.create(external_id="2", name="Chelsea", competition="Premier League")
        self.madrid = FootballTeam.objects.create(external_id="3", name="Real Madrid", competition="La Liga")

        # A past, finished result and a future, scheduled fixture for Arsenal.
        self.result = FootballFixture.objects.create(
            external_id="r", home_team=self.arsenal, away_team=self.chelsea,
            competition="Premier League", league_external_id=39,
            kickoff_at=self.now - timedelta(days=3), status=FootballFixture.Status.FINISHED,
            home_score=2, away_score=1,
        )
        self.upcoming = FootballFixture.objects.create(
            external_id="u", home_team=self.chelsea, away_team=self.arsenal,
            competition="Premier League", league_external_id=39,
            kickoff_at=self.now + timedelta(days=3), status=FootballFixture.Status.SCHEDULED,
        )
        self.laliga = FootballFixture.objects.create(
            external_id="l", home_team=self.madrid, away_team=self.chelsea,
            competition="La Liga", league_external_id=140,
            kickoff_at=self.now + timedelta(days=5), status=FootballFixture.Status.SCHEDULED,
        )

    def test_fixtures_list_public_and_ordered(self):
        response = self.client.get("/api/v1/football/fixtures/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        kickoffs = [row["kickoff_at"] for row in response.data["results"]]
        self.assertEqual(kickoffs, sorted(kickoffs))  # default order by kickoff asc

    def test_team_filter_matches_home_and_away(self):
        response = self.client.get("/api/v1/football/fixtures/", {"team": self.arsenal.id})
        ids = {row["external_id"] for row in response.data["results"]}
        self.assertEqual(ids, {"r", "u"})  # Arsenal plays home in r, away in u

    def test_competition_and_status_and_date_filters(self):
        laliga = self.client.get("/api/v1/football/fixtures/", {"competition": "La Liga"})
        self.assertEqual([r["external_id"] for r in laliga.data["results"]], ["l"])

        finished = self.client.get("/api/v1/football/fixtures/", {"status": "finished"})
        self.assertEqual([r["external_id"] for r in finished.data["results"]], ["r"])

        today = timezone.localdate()
        future = self.client.get("/api/v1/football/fixtures/", {"date_from": today.isoformat()})
        self.assertEqual({r["external_id"] for r in future.data["results"]}, {"u", "l"})

    def test_fixture_detail_and_404(self):
        response = self.client.get(f"/api/v1/football/fixtures/{self.result.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["content_type"], "football_fixture")
        self.assertEqual(response.data["home_team"]["name"], "Arsenal")
        self.assertEqual(self.client.get("/api/v1/football/fixtures/999999/").status_code, 404)

    def test_teams_list_search_and_competition_filter(self):
        search = self.client.get("/api/v1/football/teams/", {"search": "Real"})
        self.assertEqual([t["name"] for t in search.data["results"]], ["Real Madrid"])
        comp = self.client.get("/api/v1/football/teams/", {"competition": "Premier League"})
        self.assertEqual({t["name"] for t in comp.data["results"]}, {"Arsenal", "Chelsea"})

    def test_team_detail_next_fixtures_and_recent_results(self):
        response = self.client.get(f"/api/v1/football/teams/{self.arsenal.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([f["external_id"] for f in response.data["next_fixtures"]], ["u"])
        self.assertEqual([f["external_id"] for f in response.data["recent_results"]], ["r"])

    def test_competitions_list(self):
        response = self.client.get("/api/v1/football/competitions/")
        self.assertEqual(response.status_code, 200)
        by_name = {row["competition"]: row for row in response.data}
        self.assertEqual(by_name["Premier League"]["fixture_count"], 2)
        self.assertEqual(by_name["La Liga"]["fixture_count"], 1)
        self.assertEqual(by_name["Premier League"]["league_external_id"], 39)
