"""Tests for notification detection, generation, email dispatch and the API."""

from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from anime.models import Anime, AnimeEpisode
from games.models import Game
from library.models import Following
from movies.models import Movie
from notifications import events, services
from notifications import tasks as notification_tasks
from notifications.models import Notification, NotificationPreference
from sports.models import FootballFixture, FootballTeam
from tv.models import TVSeason, TVShow

User = get_user_model()


def make_user(email):
    user = User(email=email, username=email.split("@")[0] + "-x", is_email_verified=True, is_active=True)
    user.set_password("sup3r-Str0ng-pass")
    user.save()
    return user


def follow(user, content_type, object_id, enabled=True):
    return Following.objects.create(
        user=user, content_type=content_type, object_id=object_id, notifications_enabled=enabled
    )


# --- detectors --------------------------------------------------------------

class DetectorTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.today = self.now.date()

    def test_released_window_boundaries(self):
        Movie.objects.create(external_id="in", title="Recent", release_date=self.today - timedelta(days=3))
        Movie.objects.create(external_id="old", title="Old", release_date=self.today - timedelta(days=4))
        Movie.objects.create(external_id="fut", title="Future", release_date=self.today + timedelta(days=1))
        Game.objects.create(external_id="g", title="GameOut", release_date=self.today)
        found = {(e.content_type, e.title) for e in events.detect_released(self.now)}
        self.assertIn(("movie", "Recent is out"), found)
        self.assertIn(("game", "GameOut is out"), found)
        self.assertNotIn(("movie", "Old is out"), found)
        self.assertNotIn(("movie", "Future is out"), found)

    def test_release_changed(self):
        Movie.objects.create(
            external_id="c", title="Shifted",
            release_date=self.today + timedelta(days=10), previous_release_date=self.today,
        )
        Movie.objects.create(
            external_id="same", title="Same",
            release_date=self.today, previous_release_date=self.today,
        )
        found = events.detect_release_changed(self.now)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].kind, Notification.Kind.UPDATE)
        self.assertIn(str((self.today + timedelta(days=10))), found[0].event_key)

    def test_anime_episode_detection(self):
        anime = Anime.objects.create(external_id="a", title="Show")
        aired = AnimeEpisode.objects.create(anime=anime, episode_number=1, aired_at=self.now - timedelta(hours=1))
        AnimeEpisode.objects.create(anime=anime, episode_number=2, aired_at=self.now + timedelta(hours=1))  # future
        AnimeEpisode.objects.create(anime=anime, episode_number=3, aired_at=None)  # unknown
        AnimeEpisode.objects.create(anime=anime, episode_number=4, aired_at=self.now, notified=True)  # done
        found = events.detect_anime_episodes(self.now)
        self.assertEqual([e.flip_episode_id for e in found], [aired.id])
        self.assertEqual(found[0].kind, Notification.Kind.RELEASE)

    def test_football_reminder_and_result(self):
        home = FootballTeam.objects.create(external_id="h", name="Home")
        away = FootballTeam.objects.create(external_id="a", name="Away")
        soon = FootballFixture.objects.create(
            external_id="s", home_team=home, away_team=away,
            kickoff_at=self.now + timedelta(hours=5), status=FootballFixture.Status.SCHEDULED,
        )
        done = FootballFixture.objects.create(
            external_id="d", home_team=home, away_team=away,
            kickoff_at=self.now - timedelta(hours=5), status=FootballFixture.Status.FINISHED,
            home_score=2, away_score=0,
        )
        FootballFixture.objects.create(
            external_id="far", home_team=home, away_team=away,
            kickoff_at=self.now + timedelta(days=5), status=FootballFixture.Status.SCHEDULED,
        )
        by_key = {e.event_key: e for e in events.detect_football(self.now)}
        self.assertIn(f"match_reminder:{soon.id}", by_key)
        self.assertIn(f"match_result:{done.id}", by_key)
        self.assertNotIn(f"match_reminder:{soon.id + 100}", by_key)
        # Reminder audience is both teams.
        self.assertEqual(
            set(by_key[f"match_reminder:{soon.id}"].audience),
            {("football", home.id), ("football", away.id)},
        )

    def test_tv_episode_and_season(self):
        show = TVShow.objects.create(
            external_id="t", title="Series", next_episode_air_date=self.today,
            next_episode_season=2, next_episode_number=5,
        )
        TVSeason.objects.create(show=show, season_number=2, air_date=self.today)
        kinds = sorted(e.kind for e in events.detect_tv(self.now))
        self.assertEqual(kinds, [Notification.Kind.RELEASE, Notification.Kind.UPDATE])

    def test_collect_isolates_a_failing_detector(self):
        Movie.objects.create(external_id="m", title="Out", release_date=self.today)
        boom = mock.Mock(side_effect=RuntimeError("boom"))
        with mock.patch.object(events, "DETECTORS", (boom, events.detect_released)):
            with self.assertLogs("notifications.events", level="ERROR"):
                collected = events.collect_events(self.now)
        self.assertTrue(any(e.content_type == "movie" for e in collected))  # survivor ran


# --- generation -------------------------------------------------------------

class GenerateTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.today = self.now.date()
        self.user = make_user("fan@example.com")
        self.movie = Movie.objects.create(external_id="m", title="Blockbuster", release_date=self.today, genres=["Action"])

    def test_creates_in_app_and_email_rows_and_is_idempotent(self):
        follow(self.user, "movie", self.movie.id)
        services.generate_notifications(now=self.now)
        channels = set(
            Notification.objects.filter(user=self.user).values_list("channel", flat=True)
        )
        self.assertEqual(channels, {"in_app", "email"})
        services.generate_notifications(now=self.now)  # second run must not duplicate
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 2)

    def test_only_followers_with_notifications_enabled(self):
        stranger = make_user("stranger@example.com")
        muted_follower = make_user("muted@example.com")
        follow(self.user, "movie", self.movie.id)
        follow(muted_follower, "movie", self.movie.id, enabled=False)
        services.generate_notifications(now=self.now)
        self.assertTrue(Notification.objects.filter(user=self.user).exists())
        self.assertFalse(Notification.objects.filter(user=muted_follower).exists())
        self.assertFalse(Notification.objects.filter(user=stranger).exists())

    def test_preferences_filter_kind_channel_and_genre(self):
        kind_off = make_user("kind@example.com")
        chan_off = make_user("chan@example.com")
        genre_off = make_user("genre@example.com")
        for u in (kind_off, chan_off, genre_off):
            follow(u, "movie", self.movie.id)
        NotificationPreference.objects.create(user=kind_off, notify_releases=False)
        NotificationPreference.objects.create(user=chan_off, email_enabled=False)
        NotificationPreference.objects.create(user=genre_off, muted_genres=["Action"])
        services.generate_notifications(now=self.now)
        self.assertFalse(Notification.objects.filter(user=kind_off).exists())  # kind muted
        self.assertEqual(  # only in-app, email channel disabled
            list(Notification.objects.filter(user=chan_off).values_list("channel", flat=True)), ["in_app"]
        )
        self.assertFalse(Notification.objects.filter(user=genre_off).exists())  # genre muted

    def test_football_audience_is_either_team_follower(self):
        home = FootballTeam.objects.create(external_id="h", name="Home")
        away = FootballTeam.objects.create(external_id="a", name="Away")
        FootballFixture.objects.create(
            external_id="s", home_team=home, away_team=away,
            kickoff_at=self.now + timedelta(hours=2), status=FootballFixture.Status.SCHEDULED,
        )
        follow(self.user, "football", away.id)  # follows the away team only
        services.generate_notifications(now=self.now)
        self.assertTrue(
            Notification.objects.filter(user=self.user, kind=Notification.Kind.SCHEDULE).exists()
        )

    def test_anime_flip_is_atomic_with_row_insert(self):
        anime = Anime.objects.create(external_id="a", title="Anime")
        episode = AnimeEpisode.objects.create(anime=anime, episode_number=1, aired_at=self.now - timedelta(hours=1))
        follow(self.user, "anime", anime.id)
        services.generate_notifications(now=self.now)
        episode.refresh_from_db()
        self.assertTrue(episode.notified)
        self.assertTrue(Notification.objects.filter(user=self.user, content_type="anime").exists())

    def test_anime_flip_rolls_back_if_insert_fails(self):
        anime = Anime.objects.create(external_id="a", title="Anime")
        episode = AnimeEpisode.objects.create(anime=anime, episode_number=1, aired_at=self.now - timedelta(hours=1))
        follow(self.user, "anime", anime.id)
        with mock.patch.object(Notification.objects, "bulk_create", side_effect=RuntimeError("db down")):
            with self.assertRaises(RuntimeError):
                services.generate_notifications(now=self.now)
        episode.refresh_from_db()
        self.assertFalse(episode.notified)  # flag did not flip without the row


# --- dispatch ---------------------------------------------------------------

class DispatchTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.user = make_user("mail@example.com")
        mail.outbox.clear()

    def _email_row(self, title, event_key):
        return Notification.objects.create(
            user=self.user, kind=Notification.Kind.RELEASE, content_type="movie", object_id=1,
            title=title, channel=Notification.Channel.EMAIL, event_key=event_key,
        )

    def test_digest_groups_one_email_per_user_and_marks_sent(self):
        self._email_row("First", "e1")
        self._email_row("Second", "e2")
        sent = services.dispatch_notifications(now=self.now)
        self.assertEqual(sent, 2)
        self.assertEqual(len(mail.outbox), 1)  # one digest, both items
        self.assertIn("First", mail.outbox[0].body)
        self.assertIn("Second", mail.outbox[0].body)
        self.assertEqual(Notification.objects.filter(sent_at__isnull=True).count(), 0)

    def test_batch_size_caps_rows_per_run(self):
        self._email_row("A", "e1")
        self._email_row("B", "e2")
        with mock.patch.object(services, "EMAIL_BATCH", 1):
            sent = services.dispatch_notifications(now=self.now)
        self.assertEqual(sent, 1)
        self.assertEqual(Notification.objects.filter(sent_at__isnull=True).count(), 1)

    def test_rows_older_than_max_age_are_ignored(self):
        row = self._email_row("Stale", "e1")
        Notification.objects.filter(id=row.id).update(created_at=self.now - timedelta(days=3))
        sent = services.dispatch_notifications(now=self.now)
        self.assertEqual(sent, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_failure_leaves_row_pending(self):
        self._email_row("X", "e1")
        with mock.patch.object(services, "send_mail", side_effect=RuntimeError("smtp down")):
            with self.assertLogs("notifications.services", level="ERROR"):
                sent = services.dispatch_notifications(now=self.now)
        self.assertEqual(sent, 0)
        self.assertEqual(Notification.objects.filter(sent_at__isnull=True).count(), 1)  # retry next run


# --- endpoints --------------------------------------------------------------

class EndpointTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user("owner@example.com")
        self.other = make_user("other@example.com")
        self.client.force_authenticate(self.user)
        self.movie = Movie.objects.create(external_id="m", title="Flick")
        self.n1 = self._notif("one", "k1", kind=Notification.Kind.RELEASE)
        self.n2 = self._notif("two", "k2", kind=Notification.Kind.UPDATE)

    def _notif(self, title, key, *, user=None, kind=Notification.Kind.RELEASE, channel=Notification.Channel.IN_APP):
        return Notification.objects.create(
            user=user or self.user, kind=kind, content_type="movie", object_id=self.movie.id,
            title=title, channel=channel, event_key=key,
        )

    def test_list_shows_only_own_in_app_with_item(self):
        self._notif("email-only", "ek", channel=Notification.Channel.EMAIL)
        self._notif("theirs", "tk", user=self.other)
        response = self.client.get("/api/v1/notifications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)  # in-app, own only
        self.assertEqual(response.data["results"][0]["item"]["title"], "Flick")

    def test_unread_and_kind_filters(self):
        self.n1.read_at = timezone.now()
        self.n1.save(update_fields=["read_at"])
        unread = self.client.get("/api/v1/notifications/", {"unread": "true"})
        self.assertEqual([r["title"] for r in unread.data["results"]], ["two"])
        releases = self.client.get("/api/v1/notifications/", {"kind": "release"})
        self.assertEqual([r["title"] for r in releases.data["results"]], ["one"])

    def test_unread_count(self):
        self.assertEqual(self.client.get("/api/v1/notifications/unread-count/").data["count"], 2)
        self.client.post(f"/api/v1/notifications/{self.n1.id}/read/")
        self.assertEqual(self.client.get("/api/v1/notifications/unread-count/").data["count"], 1)

    def test_read_all(self):
        self.assertEqual(self.client.post("/api/v1/notifications/read-all/").data["marked_read"], 2)
        self.assertEqual(self.client.get("/api/v1/notifications/unread-count/").data["count"], 0)

    def test_mark_and_delete_other_users_is_404(self):
        theirs = self._notif("theirs", "tk", user=self.other)
        self.assertEqual(self.client.post(f"/api/v1/notifications/{theirs.id}/read/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/v1/notifications/{theirs.id}/").status_code, 404)
        self.assertTrue(Notification.objects.filter(id=theirs.id).exists())

    def test_delete_own(self):
        self.assertEqual(self.client.delete(f"/api/v1/notifications/{self.n1.id}/").status_code, 204)
        self.assertFalse(Notification.objects.filter(id=self.n1.id).exists())

    def test_preferences_get_creates_then_patch(self):
        self.assertEqual(NotificationPreference.objects.filter(user=self.user).count(), 0)
        get = self.client.get("/api/v1/users/me/preferences/notifications/")
        self.assertEqual(get.status_code, 200)
        self.assertTrue(get.data["notify_releases"])
        patch = self.client.patch(
            "/api/v1/users/me/preferences/notifications/",
            {"notify_releases": False, "muted_genres": ["Horror", " horror ", "Comedy"]},
            format="json",
        )
        self.assertFalse(patch.data["notify_releases"])
        self.assertEqual(patch.data["muted_genres"], ["Horror", "Comedy"])  # trimmed + de-duped

    def test_anonymous_is_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/notifications/").status_code, 401)


class TaskTests(TestCase):
    def test_generate_task_delegates_to_service(self):
        with mock.patch.object(notification_tasks, "generate_notifications", return_value=3) as gen:
            self.assertEqual(notification_tasks.generate_notifications_task(), 3)
            gen.assert_called_once_with()

    def test_dispatch_task_delegates_to_service(self):
        with mock.patch.object(notification_tasks, "dispatch_notifications", return_value=1) as dispatch:
            self.assertEqual(notification_tasks.dispatch_notifications_task(), 1)
            dispatch.assert_called_once_with()
