"""Tests for the discovery endpoints: search, trending, genre metadata, dashboard."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import GenrePreference
from anime.models import Anime
from content.services import SEARCH_PER_TYPE_LIMIT
from games.models import Game
from library.models import Favorite, Following
from movies.models import Movie
from recommendations.models import Recommendation
from sports.models import FootballFixture, FootballTeam

User = get_user_model()


class DiscoveryTestCase(APITestCase):
    def setUp(self):
        cache.clear()  # genres are cached; keep tests independent


class SearchTests(DiscoveryTestCase):
    def test_short_query_is_400(self):
        self.assertEqual(self.client.get("/api/v1/search/", {"q": "a"}).status_code, 400)
        self.assertEqual(self.client.get("/api/v1/search/").status_code, 400)

    def test_prefix_ranks_above_substring(self):
        # Both match "bat"; only the first starts with it, so it must sort first,
        # even though the substring match is far more popular.
        Movie.objects.create(external_id="p", title="Batman Begins", popularity=1.0)
        Movie.objects.create(external_id="s", title="The Batman", popularity=1000.0)
        results = self.client.get("/api/v1/search/", {"q": "bat"}).data["results"]
        self.assertEqual([r["title"] for r in results], ["Batman Begins", "The Batman"])

    def test_popularity_breaks_ties_within_prefix_rank(self):
        Movie.objects.create(external_id="a", title="Space Odyssey", popularity=5.0)
        Movie.objects.create(external_id="b", title="Space Jam", popularity=50.0)
        results = self.client.get("/api/v1/search/", {"q": "space"}).data["results"]
        self.assertEqual([r["title"] for r in results], ["Space Jam", "Space Odyssey"])

    def test_type_filter_limits_to_one_type(self):
        Movie.objects.create(external_id="m", title="Dragon Age")
        Game.objects.create(external_id="g", title="Dragon Quest")
        results = self.client.get("/api/v1/search/", {"q": "dragon", "type": "game"}).data["results"]
        self.assertEqual([r["content_type"] for r in results], ["game"])

    def test_unknown_type_is_400(self):
        self.assertEqual(self.client.get("/api/v1/search/", {"q": "ab", "type": "podcast"}).status_code, 400)

    def test_team_names_are_searchable(self):
        FootballTeam.objects.create(external_id="t", name="Arsenal", competition="Premier League")
        results = self.client.get("/api/v1/search/", {"q": "arsenal"}).data["results"]
        self.assertEqual(results[0]["content_type"], "football")
        self.assertEqual(results[0]["title"], "Arsenal")

    def test_per_type_cap(self):
        for i in range(SEARCH_PER_TYPE_LIMIT + 5):
            Movie.objects.create(external_id=f"c{i}", title=f"Caper {i}", popularity=float(i))
        results = self.client.get("/api/v1/search/", {"q": "caper"}).data["results"]
        self.assertEqual(len(results), SEARCH_PER_TYPE_LIMIT)


class TrendingTests(DiscoveryTestCase):
    def test_trending_shape(self):
        Movie.objects.create(external_id="m1", title="Trend Movie", trending_rank=1)
        Movie.objects.create(external_id="m2", title="Not Trending")
        Anime.objects.create(external_id="a1", title="Trend Anime", trending_rank=1)
        home = FootballTeam.objects.create(external_id="h", name="Home")
        away = FootballTeam.objects.create(external_id="w", name="Away")
        FootballFixture.objects.create(
            external_id="f1", home_team=home, away_team=away,
            kickoff_at=timezone.now() + timedelta(days=2), status=FootballFixture.Status.SCHEDULED,
        )
        data = self.client.get("/api/v1/trending/").data
        self.assertEqual({"movie", "tv", "anime", "game", "football"}, set(data))
        self.assertEqual([m["title"] for m in data["movie"]], ["Trend Movie"])  # only ranked ones
        self.assertEqual([a["title"] for a in data["anime"]], ["Trend Anime"])
        self.assertEqual(data["tv"], [])
        self.assertEqual(len(data["football"]), 1)
        self.assertEqual(data["football"][0]["home_team"]["name"], "Home")

    def test_trending_excludes_past_fixtures(self):
        home = FootballTeam.objects.create(external_id="h", name="Home")
        away = FootballTeam.objects.create(external_id="w", name="Away")
        FootballFixture.objects.create(
            external_id="past", home_team=home, away_team=away,
            kickoff_at=timezone.now() - timedelta(days=1), status=FootballFixture.Status.FINISHED,
        )
        self.assertEqual(self.client.get("/api/v1/trending/").data["football"], [])


class GenresTests(DiscoveryTestCase):
    def test_distinct_sorted_per_type(self):
        Movie.objects.create(external_id="m1", title="A", genres=["Action", "Horror"])
        Movie.objects.create(external_id="m2", title="B", genres=["Action", "Comedy"])
        Game.objects.create(external_id="g1", title="G", genres=["RPG"])
        data = self.client.get("/api/v1/meta/genres/").data
        self.assertEqual(data["movie"], ["Action", "Comedy", "Horror"])  # distinct and sorted
        self.assertEqual(data["game"], ["RPG"])
        self.assertEqual(data["tv"], [])

    def test_type_filter(self):
        Movie.objects.create(external_id="m1", title="A", genres=["Action"])
        data = self.client.get("/api/v1/meta/genres/", {"type": "movie"}).data
        self.assertEqual(list(data), ["movie"])
        self.assertEqual(data["movie"], ["Action"])

    def test_football_type_is_400(self):
        self.assertEqual(self.client.get("/api/v1/meta/genres/", {"type": "football"}).status_code, 400)


class DashboardTests(APITestCase):
    SECTIONS = {
        "in_cinemas", "upcoming_movies", "upcoming_tv", "anime_airing", "upcoming_games",
        "my_fixtures", "favorites_updates", "recommendations", "unread_notifications",
    }

    def setUp(self):
        cache.clear()
        self.today = timezone.localdate()
        self.user = self._user("dash@example.com")
        self.client.force_authenticate(self.user)

    def _user(self, email):
        u = User(email=email, username=email.split("@")[0] + "-x", is_email_verified=True, is_active=True)
        u.set_password("sup3r-Str0ng-pass")
        u.save()
        return u

    def _populate(self, suffix=""):
        Movie.objects.create(external_id=f"cine{suffix}", title="In Cinemas",
                             release_date=self.today - timedelta(days=1), genres=["Action"], popularity=5.0)
        Movie.objects.create(external_id=f"soon{suffix}", title="Coming Soon",
                             release_date=self.today + timedelta(days=10), genres=["Drama"], popularity=5.0)
        Game.objects.create(external_id=f"game{suffix}", title="New Game",
                            release_date=self.today + timedelta(days=7))

    def test_shape_and_anonymous(self):
        self.assertEqual(self.client.get("/api/v1/dashboard/").status_code, 200)
        data = self.client.get("/api/v1/dashboard/").data
        self.assertEqual(set(data), self.SECTIONS)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/dashboard/").status_code, 401)

    def test_empty_user_falls_back_to_popular(self):
        self._populate()
        data = self.client.get("/api/v1/dashboard/").data
        self.assertEqual([m["title"] for m in data["in_cinemas"]], ["In Cinemas"])
        self.assertEqual([m["title"] for m in data["upcoming_movies"]], ["Coming Soon"])
        self.assertEqual(data["unread_notifications"], 0)

    def test_personalised_by_genre(self):
        Movie.objects.create(external_id="h", title="Horror Pick",
                             release_date=self.today + timedelta(days=3), genres=["Horror"], popularity=1.0)
        Movie.objects.create(external_id="c", title="Comedy Pick",
                             release_date=self.today + timedelta(days=4), genres=["Comedy"], popularity=99.0)
        GenrePreference.objects.create(user=self.user, content_type="movie", genre="Horror")
        data = self.client.get("/api/v1/dashboard/").data
        self.assertEqual([m["title"] for m in data["upcoming_movies"]], ["Horror Pick"])  # genre beats popularity

    def test_my_fixtures_and_favorites_and_recommendations(self):
        home = FootballTeam.objects.create(external_id="h", name="Home")
        away = FootballTeam.objects.create(external_id="a", name="Away")
        fixture = FootballFixture.objects.create(
            external_id="fx", home_team=home, away_team=away,
            kickoff_at=timezone.now() + timedelta(days=2), status=FootballFixture.Status.SCHEDULED,
        )
        Following.objects.create(user=self.user, content_type="football", object_id=home.id)
        fav_movie = Movie.objects.create(external_id="fav", title="Fav Soon",
                                         release_date=self.today + timedelta(days=5))
        Favorite.objects.create(user=self.user, content_type="movie", object_id=fav_movie.id)
        Recommendation.objects.create(user=self.user, content_type="movie", object_id=fav_movie.id,
                                      score=9.0, reason="Because you like Drama")
        data = self.client.get("/api/v1/dashboard/").data
        self.assertEqual([f["id"] for f in data["my_fixtures"]], [fixture.id])
        self.assertIn(("movie", fav_movie.id), {(r["content_type"], r["id"]) for r in data["favorites_updates"]})
        self.assertEqual(data["recommendations"][0]["reason"], "Because you like Drama")
        self.assertEqual(data["recommendations"][0]["item"]["title"], "Fav Soon")

    def test_query_count_is_constant_regardless_of_volume(self):
        self._populate("-a")
        with self.assertNumQueries(11):
            self.client.get("/api/v1/dashboard/")
        for i in range(20):  # much more data
            self._populate(f"-bulk{i}")
        with self.assertNumQueries(11):
            self.client.get("/api/v1/dashboard/")
