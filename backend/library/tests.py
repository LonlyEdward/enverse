"""Tests for the personal library endpoints."""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase

from games.models import Game
from library.models import Favorite, Following
from movies.models import Movie
from sports.models import FootballTeam

User = get_user_model()


class LibraryTestCase(APITestCase):
    def setUp(self):
        cache.clear()  # reset DRF throttle counters between tests
        self.user = self._make_user("owner@example.com")
        self.other = self._make_user("other@example.com")
        self.client.force_authenticate(self.user)
        self.movie = Movie.objects.create(external_id="m1", title="Interstellar", release_date=date(2014, 11, 7))
        self.game = Game.objects.create(external_id="g1", title="Elden Ring")
        self.team = FootballTeam.objects.create(external_id="t1", name="Arsenal", competition="Premier League")

    def _make_user(self, email, verified=True):
        user = User(email=email, username=email.split("@")[0] + "-x", is_email_verified=verified, is_active=True)
        user.set_password("sup3r-Str0ng-pass")
        user.save()
        return user


class CreateAndIdempotencyTests(LibraryTestCase):
    def test_create_returns_201_then_200(self):
        payload = {"content_type": "movie", "object_id": self.movie.id}
        first = self.client.post("/api/v1/library/favorites/", payload)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.data["item"]["title"], "Interstellar")
        second = self.client.post("/api/v1/library/favorites/", payload)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Favorite.objects.filter(user=self.user).count(), 1)

    def test_invalid_content_type_is_400(self):
        response = self.client.post("/api/v1/library/favorites/", {"content_type": "podcast", "object_id": 1})
        self.assertEqual(response.status_code, 400)
        self.assertIn("content_type", response.data)

    def test_nonexistent_item_is_400(self):
        response = self.client.post("/api/v1/library/favorites/", {"content_type": "movie", "object_id": 999999})
        self.assertEqual(response.status_code, 400)
        self.assertIn("object_id", response.data)

    def test_football_team_can_be_favorited_and_followed(self):
        fav = self.client.post("/api/v1/library/favorites/", {"content_type": "football", "object_id": self.team.id})
        self.assertEqual(fav.status_code, 201)
        self.assertEqual(fav.data["item"]["title"], "Arsenal")
        follow = self.client.post("/api/v1/library/following/", {"content_type": "football", "object_id": self.team.id})
        self.assertEqual(follow.status_code, 201)
        self.assertTrue(follow.data["notifications_enabled"])

    def test_football_is_rejected_from_watchlist(self):
        response = self.client.post(
            "/api/v1/library/watchlist/", {"content_type": "football", "object_id": self.team.id}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("content_type", response.data)
        # A non-football item is still accepted on the watchlist.
        ok = self.client.post("/api/v1/library/watchlist/", {"content_type": "game", "object_id": self.game.id})
        self.assertEqual(ok.status_code, 201)


class ListTests(LibraryTestCase):
    def test_list_shows_only_own_rows_with_item_summaries(self):
        Favorite.objects.create(user=self.user, content_type="movie", object_id=self.movie.id)
        Favorite.objects.create(user=self.other, content_type="game", object_id=self.game.id)
        response = self.client.get("/api/v1/library/favorites/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["item"]["content_type"], "movie")

    def test_content_type_filter(self):
        Favorite.objects.create(user=self.user, content_type="movie", object_id=self.movie.id)
        Favorite.objects.create(user=self.user, content_type="game", object_id=self.game.id)
        response = self.client.get("/api/v1/library/favorites/", {"content_type": "game"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["object_id"], self.game.id)

    def test_list_has_no_n_plus_one(self):
        # The query count must not grow with the number of rows: load_content does
        # one query per content type, not per row.
        for i in range(3):
            m = Movie.objects.create(external_id=f"mm{i}", title=f"M{i}")
            Favorite.objects.create(user=self.user, content_type="movie", object_id=m.id)
        with self.assertNumQueries(3):  # page rows + pagination count + one load_content
            self.client.get("/api/v1/library/favorites/")
        for i in range(10):
            extra = Movie.objects.create(external_id=f"x{i}", title=f"X{i}")
            Favorite.objects.create(user=self.user, content_type="movie", object_id=extra.id)
        with self.assertNumQueries(3):  # unchanged despite many more rows
            self.client.get("/api/v1/library/favorites/")


class DeleteTests(LibraryTestCase):
    def test_delete_own_row(self):
        fav = Favorite.objects.create(user=self.user, content_type="movie", object_id=self.movie.id)
        response = self.client.delete(f"/api/v1/library/favorites/{fav.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Favorite.objects.filter(id=fav.id).exists())

    def test_delete_another_users_row_is_404(self):
        fav = Favorite.objects.create(user=self.other, content_type="movie", object_id=self.movie.id)
        response = self.client.delete(f"/api/v1/library/favorites/{fav.id}/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Favorite.objects.filter(id=fav.id).exists())  # untouched


class FollowingPatchTests(LibraryTestCase):
    def test_patch_toggles_notifications_only(self):
        follow = Following.objects.create(user=self.user, content_type="movie", object_id=self.movie.id)
        response = self.client.patch(
            f"/api/v1/library/following/{follow.id}/",
            {"notifications_enabled": False, "content_type": "game", "object_id": self.game.id},
        )
        self.assertEqual(response.status_code, 200)
        follow.refresh_from_db()
        self.assertFalse(follow.notifications_enabled)
        # The item it points at cannot be reassigned through PATCH.
        self.assertEqual(follow.content_type, "movie")
        self.assertEqual(follow.object_id, self.movie.id)

    def test_patch_another_users_follow_is_404(self):
        follow = Following.objects.create(user=self.other, content_type="movie", object_id=self.movie.id)
        response = self.client.patch(f"/api/v1/library/following/{follow.id}/", {"notifications_enabled": False})
        self.assertEqual(response.status_code, 404)


class StatusTests(LibraryTestCase):
    def test_status_reports_button_states(self):
        Favorite.objects.create(user=self.user, content_type="movie", object_id=self.movie.id)
        Following.objects.create(
            user=self.user, content_type="movie", object_id=self.movie.id, notifications_enabled=False
        )
        response = self.client.get(
            "/api/v1/library/status/", {"content_type": "movie", "object_id": self.movie.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "favorite": True,
                "watchlist": False,
                "bookmark": False,
                "following": True,
                "notifications_enabled": False,
            },
        )

    def test_status_requires_valid_params(self):
        self.assertEqual(self.client.get("/api/v1/library/status/").status_code, 400)
        self.assertEqual(
            self.client.get("/api/v1/library/status/", {"content_type": "bad", "object_id": "1"}).status_code, 400
        )


class PermissionTests(LibraryTestCase):
    def test_unverified_user_gets_403_with_code(self):
        unverified = self._make_user("new@example.com", verified=False)
        self.client.force_authenticate(unverified)
        response = self.client.get("/api/v1/library/favorites/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "email_not_verified")

    def test_anonymous_gets_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/library/favorites/").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/library/status/").status_code, 401)
