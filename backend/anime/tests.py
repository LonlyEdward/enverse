"""Tests for the anime sync, episode bookkeeping and public endpoints.

AniList is never called for real; a FakeAniList (and, for the client's own error
handling, a fake session) stand in.
"""

from datetime import date, datetime, timedelta, timezone as dt_timezone
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from anime.mappers import map_airing_status, map_media, map_season
from anime.models import Anime, AnimeEpisode
from anime.services import current_season, sync_episodes
from anime.tasks import sync_anime
from core.anilist import AniListClient, AniListError
from core.models import SyncLog


def node(anime_id, status="RELEASING", next_ep=None, episodes=12, **overrides):
    data = {
        "id": anime_id,
        "title": {"english": f"Anime {anime_id}", "romaji": f"R{anime_id}", "native": "N"},
        "description": "A description.",
        "coverImage": {"large": f"https://img/{anime_id}.jpg"},
        "bannerImage": f"https://banner/{anime_id}.jpg",
        "genres": ["Action", "Adventure"],
        "averageScore": 80,
        "popularity": 1000,
        "status": status,
        "season": "SPRING",
        "seasonYear": 2025,
        "episodes": episodes,
        "studios": {"nodes": [{"name": "MAPPA"}]},
        "nextAiringEpisode": next_ep,
    }
    data.update(overrides)
    return data


class FakeAniList:
    is_configured = True

    def __init__(self, releasing=None, upcoming=None, trending=None):
        self._releasing = releasing or []
        self._upcoming = upcoming or []
        self._trending = trending or []

    def fetch_media_page(self, *, status=None, season=None, season_year=None, sort=None, page=1, per_page=50):
        if sort and "TRENDING_DESC" in sort:
            return self._trending
        if status == "RELEASING":
            return self._releasing
        if status == "NOT_YET_RELEASED":
            return self._upcoming
        return []


# --- client error handling --------------------------------------------------

class _Resp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload


class _Session:
    def __init__(self, resp):
        self._resp = resp

    def post(self, url, json=None):
        return self._resp


class AniListClientTests(SimpleTestCase):
    def test_200_with_errors_array_raises(self):
        client = AniListClient(session=_Session(_Resp({"errors": [{"message": "bad request"}]}, status=200)))
        with self.assertRaises(AniListError):
            client.query("q", {})

    def test_success_returns_media(self):
        payload = {"data": {"Page": {"media": [{"id": 1}]}}}
        client = AniListClient(session=_Session(_Resp(payload)))
        self.assertEqual(client.fetch_media_page(status="RELEASING"), [{"id": 1}])


# --- pure mapping -----------------------------------------------------------

class MapperTests(SimpleTestCase):
    def test_status_and_season_mapping(self):
        self.assertEqual(map_airing_status("RELEASING"), Anime.AiringStatus.RELEASING)
        self.assertEqual(map_airing_status("NOT_YET_RELEASED"), Anime.AiringStatus.NOT_YET_RELEASED)
        self.assertEqual(map_airing_status("something_else"), Anime.AiringStatus.NOT_YET_RELEASED)
        self.assertEqual(map_season("WINTER"), Anime.Season.WINTER)
        self.assertEqual(map_season("FALL"), Anime.Season.FALL)
        self.assertEqual(map_season(None), "")

    def test_map_media(self):
        ts = 1_735_000_000  # a fixed Unix timestamp
        external_id, defaults, next_ep = map_media(node(1, next_ep={"airingAt": ts, "episode": 5}))
        self.assertEqual(external_id, 1)
        self.assertEqual(defaults["title"], "Anime 1")
        self.assertEqual(defaults["rating"], 8.0)  # averageScore 80 / 10
        self.assertEqual(defaults["airing_status"], Anime.AiringStatus.RELEASING)
        self.assertEqual(defaults["season"], Anime.Season.SPRING)
        self.assertEqual(defaults["studios"], ["MAPPA"])
        self.assertEqual(defaults["next_airing_episode_number"], 5)
        self.assertEqual(defaults["next_airing_at"], datetime.fromtimestamp(ts, tz=dt_timezone.utc))
        self.assertEqual(next_ep, {"number": 5, "airing_at": defaults["next_airing_at"]})


class CurrentSeasonTests(SimpleTestCase):
    def test_boundaries(self):
        self.assertEqual(current_season(date(2025, 1, 15)), ("WINTER", 2025))
        self.assertEqual(current_season(date(2025, 12, 15)), ("WINTER", 2026))  # Dec -> next year
        self.assertEqual(current_season(date(2025, 4, 1)), ("SPRING", 2025))
        self.assertEqual(current_season(date(2025, 7, 1)), ("SUMMER", 2025))
        self.assertEqual(current_season(date(2025, 10, 1)), ("FALL", 2025))


# --- episode bookkeeping ----------------------------------------------------

class EpisodeSyncTests(TestCase):
    def test_first_seen_backfills_history_and_schedules_next(self):
        anime = Anime.objects.create(external_id="a", title="A", episodes_total=24)
        airing = timezone.now() + timedelta(days=3)
        sync_episodes(anime, next_episode_number=5, next_airing_at=airing)

        self.assertEqual(anime.episodes.count(), 5)
        # Episodes 1-4 are history: notified, no air date.
        for n in range(1, 5):
            ep = anime.episodes.get(episode_number=n)
            self.assertTrue(ep.notified)
            self.assertIsNone(ep.aired_at)
        # Episode 5 is scheduled and NOT yet notified.
        nxt = anime.episodes.get(episode_number=5)
        self.assertFalse(nxt.notified)
        self.assertEqual(nxt.aired_at, airing)

    def test_finished_anime_backfills_all_as_history(self):
        anime = Anime.objects.create(external_id="b", title="B", episodes_total=12)
        sync_episodes(anime, next_episode_number=None, next_airing_at=None)
        self.assertEqual(anime.episodes.count(), 12)
        self.assertTrue(all(ep.notified for ep in anime.episodes.all()))

    def test_routine_sync_advances_next_without_duplicating(self):
        anime = Anime.objects.create(external_id="c", title="C", episodes_total=24)
        sync_episodes(anime, 5, timezone.now() + timedelta(days=1))
        # Next week: episode 5 has aired, 6 is now scheduled.
        sync_episodes(anime, 6, timezone.now() + timedelta(days=8))
        self.assertEqual(anime.episodes.count(), 6)
        self.assertFalse(anime.episodes.get(episode_number=6).notified)
        # Episode 5 remains notified=False with its air date, for Phase 10 to emit.
        self.assertFalse(anime.episodes.get(episode_number=5).notified)
        # Idempotent re-run.
        sync_episodes(anime, 6, timezone.now() + timedelta(days=8))
        self.assertEqual(anime.episodes.count(), 6)


# --- sync task --------------------------------------------------------------

class SyncAnimeTests(TestCase):
    @mock.patch("anime.tasks.build_anilist_client")
    def test_creates_and_is_idempotent(self, build):
        build.return_value = FakeAniList(
            releasing=[node(1, next_ep={"airingAt": 1_900_000_000, "episode": 3})],
            trending=[node(2), node(1)],
        )
        sync_anime()
        self.assertEqual(Anime.objects.count(), 2)
        sync_anime()
        self.assertEqual(Anime.objects.count(), 2)
        self.assertEqual(SyncLog.objects.latest("started_at").status, SyncLog.Status.SUCCESS)

    @mock.patch("anime.tasks.build_anilist_client")
    def test_trending_ranks(self, build):
        build.return_value = FakeAniList(trending=[node(2), node(1)])
        sync_anime()
        self.assertEqual(Anime.objects.get(external_id="2").trending_rank, 1)
        self.assertEqual(Anime.objects.get(external_id="1").trending_rank, 2)


# --- endpoints --------------------------------------------------------------

class AnimeEndpointTests(APITestCase):
    def setUp(self):
        now = timezone.now()
        self.releasing = Anime.objects.create(
            external_id="r", title="Releasing One", airing_status=Anime.AiringStatus.RELEASING,
            genres=["Action"], studios=["MAPPA"], rating=8.5, season="spring", season_year=2025,
            next_airing_at=now + timedelta(days=2),
        )
        self.releasing_later = Anime.objects.create(
            external_id="r2", title="Releasing Two", airing_status=Anime.AiringStatus.RELEASING,
            genres=["Comedy"], studios=["Kyoto"], rating=7.0,
            next_airing_at=now + timedelta(days=9),
        )
        self.finished = Anime.objects.create(
            external_id="f", title="Finished", airing_status=Anime.AiringStatus.FINISHED,
            genres=["Drama"], studios=["Bones"], rating=9.0, season="fall", season_year=2024,
        )
        AnimeEpisode.objects.create(anime=self.releasing, episode_number=1, notified=True)

    def test_list_public(self):
        response = self.client.get("/api/v1/anime/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)

    def test_filters(self):
        self.assertEqual(
            [a["title"] for a in self.client.get("/api/v1/anime/", {"airing_status": "finished"}).data["results"]],
            ["Finished"],
        )
        self.assertEqual(
            [a["title"] for a in self.client.get("/api/v1/anime/", {"studio": "MAPPA"}).data["results"]],
            ["Releasing One"],
        )
        self.assertEqual(
            [a["title"] for a in self.client.get("/api/v1/anime/", {"season": "fall", "season_year": 2024}).data["results"]],
            ["Finished"],
        )
        self.assertEqual(
            [a["title"] for a in self.client.get("/api/v1/anime/", {"genre": "Action"}).data["results"]],
            ["Releasing One"],
        )

    def test_trending(self):
        self.finished.trending_rank = 1
        self.finished.save(update_fields=["trending_rank"])
        response = self.client.get("/api/v1/anime/trending/")
        self.assertEqual([a["title"] for a in response.data], ["Finished"])

    def test_airing_ordered_by_next_airing(self):
        response = self.client.get("/api/v1/anime/airing/")
        titles = [a["title"] for a in response.data["results"]]
        self.assertEqual(titles, ["Releasing One", "Releasing Two"])  # soonest first; finished excluded

    def test_detail_with_episodes(self):
        response = self.client.get(f"/api/v1/anime/{self.releasing.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["content_type"], "anime")
        self.assertEqual(len(response.data["episodes"]), 1)

    def test_episodes_endpoint_404(self):
        self.assertEqual(self.client.get("/api/v1/anime/999999/episodes/").status_code, 404)
