"""Tests for the recommendation engine (pure) and the service/API around it."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APITestCase

from accounts.models import GenrePreference
from games.models import Game
from library.models import Favorite
from movies.models import Movie
from recommendations import engine
from recommendations.models import Recommendation
from recommendations.tasks import recompute_recommendations

User = get_user_model()


# --- pure engine ------------------------------------------------------------

class EngineTests(SimpleTestCase):
    def _candidate(self, ct, oid, genres=(), rating_norm=None, popularity=0.0):
        return engine.Candidate(ct, oid, tuple(genres), rating_norm, popularity)

    def test_explicit_weight_beats_a_single_favorite(self):
        signal = engine.Signal(
            explicit=[("movie", "Sci-Fi")],
            library=[("favorite", "movie", ["Action"])],
        )
        ranked = engine.rank(
            [self._candidate("movie", 1, ["Sci-Fi"]), self._candidate("movie", 2, ["Action"])],
            signal,
        )
        self.assertEqual([c.object_id for c, _, _ in ranked], [1, 2])
        self.assertEqual(ranked[0][2], "Because you like Sci-Fi")

    def test_cross_type_factor_discounts_other_types(self):
        signal = engine.Signal(explicit=[("movie", "Sci-Fi")], library=[])
        # A game with the Sci-Fi genre gets 0.5 * 4 = 2 from cross-type.
        ranked = engine.rank([self._candidate("game", 1, ["Sci-Fi"])], signal)
        score = ranked[0][1]
        self.assertAlmostEqual(score, engine.CROSS_TYPE_FACTOR * engine.EXPLICIT_WEIGHT)

    def test_quality_outweighs_popularity(self):
        signal = engine.Signal()  # no genre signal; only quality/popularity matter
        high_rating = self._candidate("movie", 1, rating_norm=1.0, popularity=1.0)
        high_pop = self._candidate("movie", 2, rating_norm=0.0, popularity=100.0)
        ranked = engine.rank([high_rating, high_pop], signal)
        self.assertEqual(ranked[0][0].object_id, 1)  # 0.3 > 0.2

    def test_empty_signal_gives_popular_reason(self):
        ranked = engine.rank([self._candidate("movie", 1, ["Action"], popularity=5.0)], engine.Signal())
        self.assertEqual(ranked[0][2], "Popular right now")


# --- service + API ----------------------------------------------------------

class RecommendationServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = self._user("fan@example.com")

    def _user(self, email):
        u = User(email=email, username=email.split("@")[0] + "-x", is_email_verified=True, is_active=True)
        u.set_password("sup3r-Str0ng-pass")
        u.save()
        return u

    def test_cold_start_recommends_popular_items(self):
        popular = Movie.objects.create(external_id="p", title="Popular", popularity=100.0, genres=["Action"])
        Movie.objects.create(external_id="q", title="Quiet", popularity=1.0, genres=["Action"])
        recompute_recommendations()  # runs for the active user
        top = Recommendation.objects.filter(user=self.user).order_by("-score").first()
        self.assertEqual((top.content_type, top.object_id), ("movie", popular.id))
        self.assertEqual(top.reason, "Popular right now")

    def test_library_items_are_excluded(self):
        owned = Movie.objects.create(external_id="o", title="Owned", popularity=50.0)
        Movie.objects.create(external_id="n", title="New", popularity=10.0)
        Favorite.objects.create(user=self.user, content_type="movie", object_id=owned.id)
        recompute_recommendations()
        recommended = set(
            Recommendation.objects.filter(user=self.user).values_list("content_type", "object_id")
        )
        self.assertNotIn(("movie", owned.id), recommended)
        self.assertIn(("movie", Movie.objects.get(external_id="n").id), recommended)

    def test_genre_preference_lifts_matching_items(self):
        GenrePreference.objects.create(user=self.user, content_type="movie", genre="Horror")
        horror = Movie.objects.create(external_id="h", title="Horror Film", genres=["Horror"], popularity=1.0)
        Movie.objects.create(external_id="d", title="Drama", genres=["Drama"], popularity=90.0)
        recompute_recommendations()
        top = Recommendation.objects.filter(user=self.user).order_by("-score").first()
        self.assertEqual(top.object_id, horror.id)  # genre weight beats mere popularity
        self.assertEqual(top.reason, "Because you like Horror")

    def test_user_isolation(self):
        other_user = self._user("other@example.com")
        Movie.objects.create(external_id="m", title="M", popularity=5.0)
        recompute_recommendations()
        self.assertTrue(Recommendation.objects.filter(user=self.user).exists())
        self.assertTrue(Recommendation.objects.filter(user=other_user).exists())
        for rec in Recommendation.objects.all():
            self.assertIn(rec.user_id, {self.user.id, other_user.id})


class RecommendationAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User(email="api@example.com", username="api-x", is_email_verified=True, is_active=True)
        self.user.set_password("sup3r-Str0ng-pass")
        self.user.save()
        self.client.force_authenticate(self.user)
        self.movie = Movie.objects.create(external_id="m", title="Flick", popularity=10.0, genres=["Action"])

    def test_list_computes_lazily_first_time(self):
        self.assertEqual(Recommendation.objects.filter(user=self.user).count(), 0)
        response = self.client.get("/api/v1/recommendations/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["item"]["title"], "Flick")
        self.assertTrue(Recommendation.objects.filter(user=self.user).exists())  # persisted

    def test_type_filter(self):
        Game.objects.create(external_id="g", title="Game", popularity=5.0)
        self.client.post("/api/v1/recommendations/refresh/")
        movies = self.client.get("/api/v1/recommendations/", {"type": "movie"})
        self.assertTrue(all(r["content_type"] == "movie" for r in movies.data))

    def test_refresh_is_throttled(self):
        for _ in range(10):  # scope recommendations_refresh = 10/hour
            self.assertEqual(self.client.post("/api/v1/recommendations/refresh/").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/recommendations/refresh/").status_code, 429)

    def test_anonymous_is_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/recommendations/").status_code, 401)
