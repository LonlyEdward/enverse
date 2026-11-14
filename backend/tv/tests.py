"""Tests for the TV sync and the public TV endpoints. No live TMDB calls."""

from datetime import date
from unittest import mock

from django.test import SimpleTestCase, TestCase
from rest_framework.test import APITestCase

from core.models import SyncLog
from core.tmdb import TMDBError
from tv.mappers import map_detail_tv, map_list_tv, map_tv_status
from tv.models import TVSeason, TVShow, season_state
from tv.tasks import DETAIL_BATCH, sync_tv


class FakeTMDB:
    is_configured = True

    def __init__(self, on_air=None, popular=None, trending=None, genres=None, details=None, fail_on=None):
        self._on_air = on_air or []
        self._popular = popular or []
        self._trending = trending or []
        self._genres = genres or {18: "Drama", 10765: "Sci-Fi & Fantasy", 35: "Comedy"}
        self._details = details or {}
        self._fail_on = set(fail_on or ())
        self.detail_calls = 0

    def tv_genre_list(self):
        return dict(self._genres)

    def on_the_air(self, page=1):
        if "on_the_air" in self._fail_on:
            raise TMDBError("on_the_air failed")
        return {"results": self._on_air if page == 1 else []}

    def popular_tv(self, page=1):
        return {"results": self._popular if page == 1 else []}

    def trending_tv(self):
        return {"results": self._trending}

    def tv_detail(self, tv_id):
        self.detail_calls += 1
        return self._details.get(
            str(tv_id),
            {"id": tv_id, "overview": "", "genres": [], "status": "Returning Series", "seasons": [], "videos": {"results": []}},
        )

    def poster_url(self, path):
        return f"https://img/w500{path}" if path else ""

    def backdrop_url(self, path):
        return f"https://img/w1280{path}" if path else ""

    def profile_url(self, path):
        return f"https://img/w185{path}" if path else ""


def tv_item(tv_id, **overrides):
    item = {
        "id": tv_id,
        "name": f"Show {tv_id}",
        "overview": "o",
        "poster_path": f"/s{tv_id}.jpg",
        "genre_ids": [18],
        "first_air_date": "2020-01-01",
        "vote_average": 7.0,
        "popularity": 50.0,
    }
    item.update(overrides)
    return item


class SeasonStateTests(SimpleTestCase):
    today = date(2025, 6, 15)

    def test_none_or_future_air_date_is_announced(self):
        self.assertEqual(season_state(None, 2, None, self.today), TVSeason.State.ANNOUNCED)
        self.assertEqual(season_state(date(2025, 12, 1), 2, None, self.today), TVSeason.State.ANNOUNCED)

    def test_past_air_date_is_aired(self):
        self.assertEqual(season_state(date(2024, 1, 1), 1, None, self.today), TVSeason.State.AIRED)

    def test_next_episode_season_is_airing(self):
        # Even with a past air date, the season carrying the next episode is airing.
        self.assertEqual(season_state(date(2024, 1, 1), 3, 3, self.today), TVSeason.State.AIRING)


class MapperTests(SimpleTestCase):
    tmdb = FakeTMDB()

    def test_status_mapping(self):
        self.assertEqual(map_tv_status("Returning Series"), TVShow.Status.RETURNING)
        self.assertEqual(map_tv_status("Ended"), TVShow.Status.ENDED)
        self.assertEqual(map_tv_status("Canceled"), TVShow.Status.CANCELED)
        self.assertEqual(map_tv_status("In Production"), TVShow.Status.RETURNING)  # fallback

    def test_map_list_tv(self):
        external_id, defaults = map_list_tv(tv_item(1), {18: "Drama"}, self.tmdb)
        self.assertEqual(external_id, 1)
        self.assertEqual(defaults["title"], "Show 1")
        self.assertEqual(defaults["genres"], ["Drama"])
        self.assertEqual(defaults["first_air_date"], date(2020, 1, 1))

    def test_map_detail_tv(self):
        detail = {
            "overview": "o",
            "genres": [{"id": 18, "name": "Drama"}],
            "status": "Ended",
            "number_of_seasons": 3,
            "next_episode_to_air": {"air_date": "2025-07-01", "season_number": 3, "episode_number": 4},
            "seasons": [
                {"season_number": 0, "air_date": None},  # specials
                {"season_number": 1, "air_date": "2020-01-01"},
            ],
            "videos": {"results": [{"site": "YouTube", "type": "Trailer", "official": True, "key": "k"}]},
        }
        fields, seasons = map_detail_tv(detail, self.tmdb)
        self.assertEqual(fields["status"], TVShow.Status.ENDED)
        self.assertEqual(fields["number_of_seasons"], 3)
        self.assertEqual(fields["next_episode_season"], 3)
        self.assertEqual(fields["trailer_youtube_key"], "k")
        self.assertEqual(len(seasons), 2)


class SyncTVTests(TestCase):
    @mock.patch("tv.tasks.build_tmdb_client")
    def test_creates_and_is_idempotent(self, build):
        build.return_value = FakeTMDB(on_air=[tv_item(1), tv_item(2)], trending=[tv_item(2)])
        sync_tv()
        self.assertEqual(TVShow.objects.count(), 2)
        sync_tv()
        self.assertEqual(TVShow.objects.count(), 2)
        self.assertEqual(SyncLog.objects.latest("started_at").status, SyncLog.Status.SUCCESS)

    @mock.patch("tv.tasks.build_tmdb_client")
    def test_trending_ranks(self, build):
        build.return_value = FakeTMDB(trending=[tv_item(2), tv_item(1)])
        sync_tv()
        self.assertEqual(TVShow.objects.get(external_id="2").trending_rank, 1)
        self.assertEqual(TVShow.objects.get(external_id="1").trending_rank, 2)

    @mock.patch("tv.tasks.build_tmdb_client")
    def test_seasons_upserted_with_computed_state_and_idempotent(self, build):
        details = {
            "7": {
                "id": 7, "overview": "o", "genres": [], "status": "Returning Series", "number_of_seasons": 2,
                "next_episode_to_air": {"air_date": "2999-01-01", "season_number": 2, "episode_number": 1},
                "seasons": [
                    {"season_number": 1, "air_date": "2000-01-01"},  # past -> aired
                    {"season_number": 2, "air_date": "2999-01-01"},  # next-episode season -> airing
                ],
                "videos": {"results": []},
            }
        }
        build.return_value = FakeTMDB(on_air=[tv_item(7)], details=details)
        sync_tv()
        show = TVShow.objects.get(external_id="7")
        self.assertEqual(show.seasons.count(), 2)
        self.assertEqual(show.seasons.get(season_number=1).state, TVSeason.State.AIRED)
        self.assertEqual(show.seasons.get(season_number=2).state, TVSeason.State.AIRING)
        # Re-sync must not duplicate seasons.
        sync_tv()
        self.assertEqual(TVShow.objects.get(external_id="7").seasons.count(), 2)

    @mock.patch("tv.tasks.build_tmdb_client")
    def test_detail_rotation_capped(self, build):
        for i in range(DETAIL_BATCH + 5):
            TVShow.objects.create(external_id=str(i), title=f"S{i}")
        fake = FakeTMDB()
        build.return_value = fake
        sync_tv()
        self.assertEqual(fake.detail_calls, DETAIL_BATCH)

    @mock.patch("tv.tasks.build_tmdb_client")
    def test_api_failure_marks_failed(self, build):
        build.return_value = FakeTMDB(fail_on={"on_the_air"})
        sync_tv()
        self.assertEqual(SyncLog.objects.latest("started_at").status, SyncLog.Status.FAILED)

    def test_missing_key_exits_cleanly(self):
        with self.settings(TMDB_API_KEY=""):
            with self.assertLogs("tv.tasks", level="WARNING"):
                sync_tv()
        self.assertEqual(TVShow.objects.count(), 0)


class TVEndpointTests(APITestCase):
    def setUp(self):
        self.returning = TVShow.objects.create(
            external_id="r", title="Returning Show", status=TVShow.Status.RETURNING,
            genres=["Drama"], rating=8.0, popularity=90.0,
        )
        self.ended = TVShow.objects.create(
            external_id="e", title="Ended Show", status=TVShow.Status.ENDED,
            genres=["Comedy"], rating=6.0, popularity=40.0,
        )
        TVSeason.objects.create(show=self.returning, season_number=1, air_date=date(2020, 1, 1), state=TVSeason.State.AIRED)
        TVSeason.objects.create(show=self.returning, season_number=2, state=TVSeason.State.ANNOUNCED)

    def test_list_public(self):
        response = self.client.get("/api/v1/tv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)

    def test_filter_status(self):
        response = self.client.get("/api/v1/tv/", {"status": "ended"})
        self.assertEqual([s["title"] for s in response.data["results"]], ["Ended Show"])

    def test_filter_genre_and_rating(self):
        self.assertEqual(
            [s["title"] for s in self.client.get("/api/v1/tv/", {"genre": "Drama"}).data["results"]],
            ["Returning Show"],
        )
        self.assertEqual(
            [s["title"] for s in self.client.get("/api/v1/tv/", {"rating_gte": 7}).data["results"]],
            ["Returning Show"],
        )

    def test_trending(self):
        self.ended.trending_rank = 1
        self.ended.save(update_fields=["trending_rank"])
        response = self.client.get("/api/v1/tv/trending/")
        self.assertEqual([s["title"] for s in response.data], ["Ended Show"])

    def test_detail_embeds_seasons(self):
        response = self.client.get(f"/api/v1/tv/{self.returning.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["seasons"]), 2)
        self.assertEqual(response.data["content_type"], "tv")

    def test_seasons_endpoint(self):
        response = self.client.get(f"/api/v1/tv/{self.returning.id}/seasons/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_seasons_endpoint_404_for_unknown_show(self):
        response = self.client.get("/api/v1/tv/999999/seasons/")
        self.assertEqual(response.status_code, 404)
