"""Tests for the games sync and the public game endpoints. No live RAWG calls."""

from datetime import date, timedelta
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import SyncLog
from core.rawg import RAWGError
from games.mappers import extract_screenshots, extract_trailer, map_game_detail, map_list_game
from games.models import Game
from games.tasks import DETAIL_BATCH, sync_games


class FakeRAWG:
    is_configured = True

    def __init__(self, upcoming=None, recent=None, trending=None, details=None, fail_on=None):
        self._upcoming = upcoming or []
        self._recent = recent or []
        self._trending = trending or []
        self._details = details or {}
        self._fail_on = set(fail_on or ())
        self.detail_calls = 0

    def list_games(self, dates, ordering, page_size=40, page=1):
        if "list" in self._fail_on:
            raise RAWGError("list_games failed")
        if ordering == "released":
            return {"results": self._upcoming}
        if ordering == "-released":
            return {"results": self._recent}
        if ordering == "-added":
            return {"results": self._trending}
        return {"results": []}

    def game_detail(self, game_id):
        self.detail_calls += 1
        return self._details.get(str(game_id), {"description_raw": "desc", "developers": [], "metacritic": None})

    def game_screenshots(self, game_id):
        return {"results": [{"image": f"https://ss/{game_id}.jpg"}]}

    def game_movies(self, game_id):
        return {"results": [{"data": {"max": f"https://mov/{game_id}.mp4"}}]}


def rawg_item(game_id, released="2025-06-01", **overrides):
    item = {
        "id": game_id,
        "name": f"Game {game_id}",
        "background_image": f"https://img/{game_id}.jpg",
        "genres": [{"name": "Action"}],
        "platforms": [{"platform": {"name": "PC"}}, {"platform": {"name": "PS5"}}],
        "released": released,
        "rating": 4.2,
        "metacritic": 88,
        "added": 500,
    }
    item.update(overrides)
    return item


class MapperTests(SimpleTestCase):
    def test_map_list_game(self):
        external_id, defaults = map_list_game(rawg_item(1))
        self.assertEqual(external_id, 1)
        self.assertEqual(defaults["title"], "Game 1")
        self.assertEqual(defaults["platforms"], ["PC", "PS5"])
        self.assertEqual(defaults["genres"], ["Action"])
        self.assertEqual(defaults["release_date"], date(2025, 6, 1))
        self.assertEqual(defaults["rating"], 4.2)
        self.assertEqual(defaults["metacritic"], 88)
        self.assertEqual(defaults["popularity"], 500.0)

    def test_map_game_detail_and_extractors(self):
        fields = map_game_detail({"description_raw": "A game.", "developers": [{"name": "Studio"}], "metacritic": 90})
        self.assertEqual(fields["description"], "A game.")
        self.assertEqual(fields["developers"], ["Studio"])
        self.assertEqual(extract_screenshots({"results": [{"image": "a"}, {"image": "b"}]}), ["a", "b"])
        self.assertEqual(extract_trailer({"results": [{"data": {"max": "m.mp4"}}]}), "m.mp4")
        self.assertEqual(extract_trailer({"results": []}), "")


class SyncGamesTests(TestCase):
    @mock.patch("games.tasks.build_rawg_client")
    def test_creates_and_is_idempotent_with_platforms(self, build):
        build.return_value = FakeRAWG(upcoming=[rawg_item(1), rawg_item(2)], trending=[rawg_item(1)])
        sync_games()
        self.assertEqual(Game.objects.count(), 2)
        self.assertEqual(Game.objects.get(external_id="1").platforms, ["PC", "PS5"])
        sync_games()
        self.assertEqual(Game.objects.count(), 2)
        self.assertEqual(SyncLog.objects.latest("started_at").status, SyncLog.Status.SUCCESS)

    @mock.patch("games.tasks.build_rawg_client")
    def test_records_release_date_change(self, build):
        Game.objects.create(external_id="9", title="Old", release_date=date(2025, 1, 1))
        build.return_value = FakeRAWG(upcoming=[rawg_item(9, released="2026-03-03")])
        sync_games()
        game = Game.objects.get(external_id="9")
        self.assertEqual(game.release_date, date(2026, 3, 3))
        self.assertEqual(game.previous_release_date, date(2025, 1, 1))

    @mock.patch("games.tasks.build_rawg_client")
    def test_detail_rotation_capped(self, build):
        for i in range(DETAIL_BATCH + 5):
            Game.objects.create(external_id=str(i), title=f"G{i}")
        fake = FakeRAWG()
        build.return_value = fake
        sync_games()
        self.assertEqual(fake.detail_calls, DETAIL_BATCH)

    @mock.patch("games.tasks.build_rawg_client")
    def test_api_failure_marks_failed(self, build):
        build.return_value = FakeRAWG(fail_on={"list"})
        sync_games()
        self.assertEqual(SyncLog.objects.latest("started_at").status, SyncLog.Status.FAILED)

    def test_missing_key_exits_cleanly(self):
        with self.settings(RAWG_API_KEY=""):
            with self.assertLogs("games.tasks", level="WARNING"):
                sync_games()
        self.assertEqual(Game.objects.count(), 0)


class GameEndpointTests(APITestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.upcoming = Game.objects.create(
            external_id="u", title="Future Game", release_date=self.today + timedelta(days=30),
            platforms=["PC"], genres=["Action"], rating=4.5, metacritic=90, popularity=100.0,
        )
        self.released = Game.objects.create(
            external_id="r", title="Past Game", release_date=self.today - timedelta(days=30),
            platforms=["PS5"], genres=["RPG"], rating=3.0, metacritic=70, popularity=50.0,
        )

    def test_list_public(self):
        response = self.client.get("/api/v1/games/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)

    def test_platform_filter(self):
        response = self.client.get("/api/v1/games/", {"platform": "PC"})
        self.assertEqual([g["title"] for g in response.data["results"]], ["Future Game"])

    def test_status_filter(self):
        self.assertEqual(
            [g["title"] for g in self.client.get("/api/v1/games/", {"status": "upcoming"}).data["results"]],
            ["Future Game"],
        )
        self.assertEqual(
            [g["title"] for g in self.client.get("/api/v1/games/", {"status": "released"}).data["results"]],
            ["Past Game"],
        )

    def test_rating_and_date_filters(self):
        self.assertEqual(
            [g["title"] for g in self.client.get("/api/v1/games/", {"rating_gte": 4}).data["results"]],
            ["Future Game"],
        )
        response = self.client.get("/api/v1/games/", {"release_date_gte": self.today.isoformat()})
        self.assertEqual([g["title"] for g in response.data["results"]], ["Future Game"])

    def test_trending(self):
        self.released.trending_rank = 1
        self.released.save(update_fields=["trending_rank"])
        response = self.client.get("/api/v1/games/trending/")
        self.assertEqual([g["title"] for g in response.data], ["Past Game"])

    def test_detail_and_status(self):
        response = self.client.get(f"/api/v1/games/{self.upcoming.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["content_type"], "game")
        self.assertEqual(response.data["status"], "upcoming")

    def test_detail_404(self):
        self.assertEqual(self.client.get("/api/v1/games/999999/").status_code, 404)
