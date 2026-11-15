"""Tests for the unified calendar endpoint."""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from agenda.services import LIMIT_PER_SOURCE
from anime.models import Anime
from games.models import Game
from library.models import Favorite
from movies.models import Movie
from sports.models import FootballFixture, FootballTeam

User = get_user_model()


class CalendarTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.today = timezone.localdate()
        self.start = self.today.isoformat()
        self.end = (self.today + timedelta(days=30)).isoformat()
        self.movie = Movie.objects.create(external_id="m", title="Movie", release_date=self.today + timedelta(days=2))
        self.game = Game.objects.create(external_id="g", title="Game", release_date=self.today + timedelta(days=5))
        home = FootballTeam.objects.create(external_id="h", name="Home")
        away = FootballTeam.objects.create(external_id="a", name="Away")
        self.fixture = FootballFixture.objects.create(
            external_id="f", home_team=home, away_team=away,
            kickoff_at=timezone.now() + timedelta(days=3), status=FootballFixture.Status.SCHEDULED,
        )
        self.home = home

    def _get(self, **params):
        base = {"start": self.start, "end": self.end}
        base.update(params)
        return self.client.get("/api/v1/calendar/", base)

    def test_requires_valid_range(self):
        self.assertEqual(self.client.get("/api/v1/calendar/").status_code, 400)
        self.assertEqual(self.client.get("/api/v1/calendar/", {"start": "nope", "end": self.end}).status_code, 400)

    def test_end_before_start_is_400(self):
        response = self.client.get(
            "/api/v1/calendar/", {"start": self.end, "end": self.start}
        )
        self.assertEqual(response.status_code, 400)

    def test_span_limit(self):
        far = (self.today + timedelta(days=90)).isoformat()
        self.assertEqual(self.client.get("/api/v1/calendar/", {"start": self.start, "end": far}).status_code, 400)

    def test_unknown_type_is_400(self):
        self.assertEqual(self._get(type="podcast").status_code, 400)

    def test_lists_events_sorted_by_date(self):
        response = self._get()
        self.assertEqual(response.status_code, 200)
        kinds = {(r["content_type"], r["kind"]) for r in response.data["results"]}
        self.assertEqual(kinds, {("movie", "release"), ("game", "release"), ("football", "match")})
        dates = [r["datetime"] or r["date"] for r in response.data["results"]]
        self.assertEqual(dates, sorted(dates))  # ascending

    def test_type_filter_runs_one_source(self):
        response = self._get(type="movie")
        self.assertEqual({r["content_type"] for r in response.data["results"]}, {"movie"})

    def test_events_outside_range_excluded(self):
        Movie.objects.create(external_id="old", title="Old", release_date=self.today - timedelta(days=10))
        titles = {r["title"] for r in self._get(type="movie").data["results"]}
        self.assertEqual(titles, {"Movie"})

    def test_mine_requires_auth_and_filters_to_library(self):
        self.assertEqual(self._get(mine="true").status_code, 401)  # anonymous

        user = User(email="u@example.com", username="u-x", is_email_verified=True, is_active=True)
        user.set_password("sup3r-Str0ng-pass")
        user.save()
        self.client.force_authenticate(user)
        Favorite.objects.create(user=user, content_type="movie", object_id=self.movie.id)
        results = self._get(mine="true").data["results"]
        self.assertEqual({(r["content_type"], r["id"]) for r in results}, {("movie", self.movie.id)})

    def test_mine_football_follows_team_fixtures(self):
        user = User(email="fan@example.com", username="fan-x", is_email_verified=True, is_active=True)
        user.set_password("sup3r-Str0ng-pass")
        user.save()
        self.client.force_authenticate(user)
        Favorite.objects.create(user=user, content_type="football", object_id=self.home.id)
        results = self._get(mine="true", type="football").data["results"]
        self.assertEqual([r["id"] for r in results], [self.fixture.id])

    def test_per_source_limit(self):
        for i in range(LIMIT_PER_SOURCE + 5):
            Anime.objects.create(
                external_id=f"an{i}", title=f"A{i}",
                next_airing_at=timezone.now() + timedelta(days=1, minutes=i),
            )
        results = self._get(type="anime").data["results"]
        self.assertEqual(len(results), LIMIT_PER_SOURCE)
