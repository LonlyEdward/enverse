"""Tests for the movie sync and the public movie endpoints.

The live TMDB API is never called: a FakeTMDB stands in for the client, patched
where the task uses it (``movies.tasks.build_tmdb_client``).
"""

from datetime import date, timedelta
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import SyncLog
from core.tmdb import TMDBError
from movies.mappers import map_detail_movie, map_list_movie
from movies.models import Movie, movie_status
from movies.tasks import DETAIL_BATCH, sync_movies


class FakeTMDB:
    """Stand-in for TMDBClient with the same surface the sync and mappers use."""

    is_configured = True

    def __init__(self, now_playing=None, upcoming=None, trending=None, genres=None, details=None, fail_on=None):
        self._now = now_playing or []
        self._up = upcoming or []
        self._trending = trending or []
        self._genres = genres or {28: "Action", 12: "Adventure", 35: "Comedy", 18: "Drama"}
        self._details = details or {}
        self._fail_on = set(fail_on or ())
        self.detail_calls = 0

    def genre_list(self):
        if "genre_list" in self._fail_on:
            raise TMDBError("genre_list failed")
        return dict(self._genres)

    def now_playing(self, page=1):
        if "now_playing" in self._fail_on:
            raise TMDBError("now_playing failed")
        return {"results": self._now if page == 1 else []}

    def upcoming(self, page=1):
        return {"results": self._up if page == 1 else []}

    def trending_movies(self):
        return {"results": self._trending}

    def movie_detail(self, movie_id):
        self.detail_calls += 1
        return self._details.get(
            str(movie_id),
            {"id": movie_id, "overview": "", "genres": [], "videos": {"results": []}, "credits": {"cast": []}},
        )

    def poster_url(self, path):
        return f"https://img/w500{path}" if path else ""

    def backdrop_url(self, path):
        return f"https://img/w1280{path}" if path else ""

    def profile_url(self, path):
        return f"https://img/w185{path}" if path else ""


def list_item(movie_id, **overrides):
    item = {
        "id": movie_id,
        "title": f"Movie {movie_id}",
        "overview": "An overview.",
        "poster_path": f"/p{movie_id}.jpg",
        "genre_ids": [28, 35],
        "release_date": "2025-06-01",
        "vote_average": 7.5,
        "popularity": 100.0,
    }
    item.update(overrides)
    return item


# --- pure mappers -----------------------------------------------------------

class MapperTests(SimpleTestCase):
    tmdb = FakeTMDB()  # not `client`: TestCase.client is the Django test client

    def test_map_list_movie(self):
        external_id, defaults = map_list_movie(list_item(1), {28: "Action", 35: "Comedy"}, self.tmdb)
        self.assertEqual(external_id, 1)
        self.assertEqual(defaults["title"], "Movie 1")
        self.assertEqual(defaults["genres"], ["Action", "Comedy"])
        self.assertEqual(defaults["release_date"], date(2025, 6, 1))
        self.assertEqual(defaults["rating"], 7.5)
        self.assertEqual(defaults["poster_url"], "https://img/w500/p1.jpg")

    def test_map_list_movie_defaults_for_missing_fields(self):
        external_id, defaults = map_list_movie({"id": 9}, {}, self.tmdb)
        self.assertEqual(external_id, 9)
        self.assertEqual(defaults["title"], "Untitled")
        self.assertEqual(defaults["genres"], [])
        self.assertIsNone(defaults["release_date"])
        self.assertIsNone(defaults["rating"])
        self.assertEqual(defaults["poster_url"], "")

    def test_map_list_movie_without_id(self):
        external_id, _ = map_list_movie({"title": "x"}, {}, self.tmdb)
        self.assertIsNone(external_id)

    def test_map_detail_picks_official_youtube_trailer(self):
        detail = {
            "overview": "o",
            "genres": [{"id": 1, "name": "Action"}],
            "runtime": 142,
            "videos": {
                "results": [
                    {"site": "YouTube", "type": "Teaser", "official": True, "key": "teaser"},
                    {"site": "YouTube", "type": "Trailer", "official": False, "key": "fan"},
                    {"site": "YouTube", "type": "Trailer", "official": True, "key": "official"},
                ]
            },
            "credits": {"cast": [{"name": f"Actor {i}", "character": "C", "order": i} for i in range(20)]},
            "production_companies": [{"name": "Studio", "logo_path": "/l.png"}],
        }
        fields = map_detail_movie(detail, self.tmdb)
        self.assertEqual(fields["trailer_youtube_key"], "official")
        self.assertEqual(fields["runtime"], 142)
        self.assertEqual(len(fields["cast"]), 10)  # capped at top 10 by order
        self.assertEqual(fields["cast"][0]["name"], "Actor 0")
        self.assertEqual(fields["production_companies"], [{"name": "Studio", "logo_url": "https://img/w185/l.png"}])


class MovieStatusTests(SimpleTestCase):
    def test_windows(self):
        today = date(2025, 6, 15)
        self.assertEqual(movie_status(None, today), "unknown")
        self.assertEqual(movie_status(today + timedelta(days=5), today), "upcoming")
        self.assertEqual(movie_status(today - timedelta(days=10), today), "now_showing")
        self.assertEqual(movie_status(today - timedelta(days=60), today), "recent")
        self.assertEqual(movie_status(today - timedelta(days=200), today), "released")


# --- sync task --------------------------------------------------------------

class SyncMoviesTests(TestCase):
    @mock.patch("movies.tasks.build_tmdb_client")
    def test_creates_and_is_idempotent(self, build):
        build.return_value = FakeTMDB(now_playing=[list_item(1), list_item(2)], trending=[list_item(2), list_item(1)])
        sync_movies()
        self.assertEqual(Movie.objects.count(), 2)
        sync_movies()  # running twice must not duplicate
        self.assertEqual(Movie.objects.count(), 2)
        log = SyncLog.objects.filter(source=SyncLog.Source.TMDB).latest("started_at")
        self.assertEqual(log.status, SyncLog.Status.SUCCESS)

    @mock.patch("movies.tasks.build_tmdb_client")
    def test_assigns_trending_ranks(self, build):
        build.return_value = FakeTMDB(trending=[list_item(2), list_item(1)])
        sync_movies()
        self.assertEqual(Movie.objects.get(external_id="2").trending_rank, 1)
        self.assertEqual(Movie.objects.get(external_id="1").trending_rank, 2)

    @mock.patch("movies.tasks.build_tmdb_client")
    def test_records_release_date_change(self, build):
        Movie.objects.create(external_id="5", title="Old", release_date=date(2025, 1, 1))
        build.return_value = FakeTMDB(now_playing=[list_item(5, release_date="2025-12-25")])
        sync_movies()
        movie = Movie.objects.get(external_id="5")
        self.assertEqual(movie.release_date, date(2025, 12, 25))
        self.assertEqual(movie.previous_release_date, date(2025, 1, 1))

    @mock.patch("movies.tasks.build_tmdb_client")
    def test_detail_rotation_is_capped(self, build):
        for i in range(DETAIL_BATCH + 10):
            Movie.objects.create(external_id=str(i), title=f"M{i}")
        fake = FakeTMDB()  # empty lists; only the detail rotation runs
        build.return_value = fake
        sync_movies()
        self.assertEqual(fake.detail_calls, DETAIL_BATCH)

    @mock.patch("movies.tasks.build_tmdb_client")
    def test_api_failure_marks_sync_failed_without_raising(self, build):
        build.return_value = FakeTMDB(fail_on={"now_playing"})
        sync_movies()  # must not raise
        log = SyncLog.objects.filter(source=SyncLog.Source.TMDB).latest("started_at")
        self.assertEqual(log.status, SyncLog.Status.FAILED)

    def test_missing_key_exits_cleanly(self):
        with self.settings(TMDB_API_KEY=""):
            with self.assertLogs("movies.tasks", level="WARNING"):
                sync_movies()
        self.assertEqual(Movie.objects.count(), 0)
        self.assertFalse(SyncLog.objects.exists())


# --- endpoints --------------------------------------------------------------

class MovieEndpointTests(APITestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.upcoming = Movie.objects.create(
            external_id="u", title="Upcoming", release_date=self.today + timedelta(days=10),
            genres=["Action"], rating=8.0, popularity=50.0,
        )
        self.showing = Movie.objects.create(
            external_id="s", title="Showing", release_date=self.today - timedelta(days=5),
            genres=["Comedy"], rating=6.0, popularity=80.0,
        )
        self.old = Movie.objects.create(
            external_id="o", title="Oldie", release_date=self.today - timedelta(days=300),
            genres=["Action"], rating=9.0, popularity=10.0,
        )

    def test_list_is_public_and_paginated(self):
        self.client.force_authenticate(None)
        response = self.client.get("/api/v1/movies/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        self.assertIn("results", response.data)

    def test_filter_status_upcoming(self):
        response = self.client.get("/api/v1/movies/", {"status": "upcoming"})
        self.assertEqual([m["title"] for m in response.data["results"]], ["Upcoming"])

    def test_filter_genre(self):
        response = self.client.get("/api/v1/movies/", {"genre": "Action"})
        self.assertEqual(sorted(m["title"] for m in response.data["results"]), ["Oldie", "Upcoming"])

    def test_filter_rating_gte(self):
        response = self.client.get("/api/v1/movies/", {"rating_gte": 8.5})
        self.assertEqual([m["title"] for m in response.data["results"]], ["Oldie"])

    def test_filter_year(self):
        year = self.upcoming.release_date.year
        response = self.client.get("/api/v1/movies/", {"year": year})
        self.assertIn("Upcoming", [m["title"] for m in response.data["results"]])

    def test_search(self):
        response = self.client.get("/api/v1/movies/", {"search": "show"})
        self.assertEqual([m["title"] for m in response.data["results"]], ["Showing"])

    def test_ordering_by_rating(self):
        response = self.client.get("/api/v1/movies/", {"ordering": "rating"})
        ratings = [m["rating"] for m in response.data["results"]]
        self.assertEqual(ratings, sorted(ratings))

    def test_trending_order(self):
        self.showing.trending_rank = 1
        self.showing.save(update_fields=["trending_rank"])
        self.upcoming.trending_rank = 2
        self.upcoming.save(update_fields=["trending_rank"])
        response = self.client.get("/api/v1/movies/trending/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m["title"] for m in response.data], ["Showing", "Upcoming"])

    def test_detail_includes_similar_and_status(self):
        response = self.client.get(f"/api/v1/movies/{self.upcoming.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Upcoming")
        self.assertEqual(response.data["status"], "upcoming")
        # Oldie shares the "Action" genre, so it shows up as similar.
        self.assertIn("Oldie", [m["title"] for m in response.data["similar"]])

    def test_detail_404(self):
        response = self.client.get("/api/v1/movies/999999/")
        self.assertEqual(response.status_code, 404)
