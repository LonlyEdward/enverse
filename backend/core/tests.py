"""Tests for the shared sync/registry/http infrastructure.

(The Phase 0 health and env tests live in core/test_health.py and
config/test_env.py.)
"""

from datetime import date, datetime

from django.conf import settings
from django.test import SimpleTestCase, TestCase

from config.celery import celery_app
from core.filters import GenreFilterSet
from core.http import build_session
from core.models import SyncLog
from core.registry import content_type_of, get_content_model, load_content, summarize
from core.sync import SyncRun, parse_date, replace_trending_ranks, store_item
from games.models import Game
from movies.models import Movie


class ParseDateTests(SimpleTestCase):
    def test_valid_string(self):
        self.assertEqual(parse_date("2025-03-01"), date(2025, 3, 1))

    def test_empty_and_none_return_none(self):
        self.assertIsNone(parse_date(""))
        self.assertIsNone(parse_date(None))

    def test_invalid_returns_none(self):
        self.assertIsNone(parse_date("2021-13-40"))  # matched shape, impossible date
        self.assertIsNone(parse_date("not a date"))

    def test_date_and_datetime_inputs(self):
        self.assertEqual(parse_date(date(2025, 1, 2)), date(2025, 1, 2))
        self.assertEqual(parse_date(datetime(2025, 1, 2, 3, 4)), date(2025, 1, 2))


class HttpSessionTests(SimpleTestCase):
    def test_retries_all_methods_including_post(self):
        session = build_session()
        retries = session.get_adapter("https://example.com").max_retries
        # allowed_methods=None means every method is retried, POST included.
        self.assertIsNone(retries.allowed_methods)
        self.assertEqual(retries.total, 3)
        self.assertIn(429, retries.status_forcelist)
        self.assertTrue(retries.respect_retry_after_header)

    def test_user_agent_is_generic(self):
        session = build_session()
        self.assertIn("EnVerse", session.headers["User-Agent"])


class SyncRunTests(TestCase):
    source = SyncLog.Source.TMDB

    def test_success(self):
        with SyncRun(self.source) as run:
            run.processed(3)
        log = SyncLog.objects.latest("started_at")
        self.assertEqual(log.status, SyncLog.Status.SUCCESS)
        self.assertEqual(log.items_processed, 3)
        self.assertIsNotNone(log.finished_at)
        self.assertEqual(log.error_message, "")

    def test_partial_when_some_items_error_but_some_processed(self):
        with SyncRun(self.source) as run:
            run.processed(2)
            run.error("item 7 was malformed")
        log = SyncLog.objects.latest("started_at")
        self.assertEqual(log.status, SyncLog.Status.PARTIAL)
        self.assertEqual(log.items_processed, 2)
        self.assertIn("item 7", log.error_message)

    def test_total_failure_when_everything_errors(self):
        with SyncRun(self.source) as run:
            run.error("boom one")
            run.error("boom two")
        log = SyncLog.objects.latest("started_at")
        self.assertEqual(log.status, SyncLog.Status.FAILED)
        self.assertEqual(log.items_processed, 0)

    def test_exception_is_swallowed_and_recorded(self):
        # The exception must NOT propagate out of the block.
        with SyncRun(self.source) as run:
            run.processed(1)
            raise ValueError("kaboom")
        log = SyncLog.objects.latest("started_at")
        self.assertEqual(log.status, SyncLog.Status.FAILED)
        self.assertIn("kaboom", log.error_message)


class StoreItemTests(TestCase):
    def test_upsert_is_idempotent(self):
        obj1, created1 = store_item(Movie, "tmdb-1", {"title": "First"})
        obj2, created2 = store_item(Movie, "tmdb-1", {"title": "Updated"})
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(Movie.objects.count(), 1)
        obj2.refresh_from_db()
        self.assertEqual(obj2.title, "Updated")
        self.assertIsNotNone(obj2.last_synced_at)


class ReplaceTrendingRanksTests(TestCase):
    def test_assigns_new_ranks_and_clears_stale_ones(self):
        a = Movie.objects.create(external_id="a", title="A", trending_rank=5)
        b = Movie.objects.create(external_id="b", title="B")
        stale = Movie.objects.create(external_id="c", title="C", trending_rank=9)

        replace_trending_ranks(Movie, ["b", "a"])

        a.refresh_from_db()
        b.refresh_from_db()
        stale.refresh_from_db()
        self.assertEqual(b.trending_rank, 1)
        self.assertEqual(a.trending_rank, 2)
        self.assertIsNone(stale.trending_rank)  # no longer trending

    def test_empty_list_clears_all(self):
        Movie.objects.create(external_id="a", title="A", trending_rank=1)
        replace_trending_ranks(Movie, [])
        self.assertFalse(Movie.objects.filter(trending_rank__isnull=False).exists())


class RegistryTests(TestCase):
    def test_get_content_model(self):
        self.assertIs(get_content_model("movie"), Movie)
        self.assertIs(get_content_model("game"), Game)
        with self.assertRaises(ValueError):
            get_content_model("nope")

    def test_content_type_of(self):
        movie = Movie.objects.create(external_id="m", title="M")
        self.assertEqual(content_type_of(movie), "movie")

    def test_load_content_uses_one_query_per_type(self):
        m1 = Movie.objects.create(external_id="m1", title="M1")
        m2 = Movie.objects.create(external_id="m2", title="M2")
        g1 = Game.objects.create(external_id="g1", title="G1")
        pairs = [("movie", m1.id), ("movie", m2.id), ("game", g1.id)]
        with self.assertNumQueries(2):  # one for movies, one for games
            resolved = load_content(pairs)
        self.assertEqual(len(resolved), 3)
        self.assertEqual(resolved[("movie", m1.id)], m1)
        self.assertEqual(resolved[("game", g1.id)], g1)

    def test_summarize_movie(self):
        movie = Movie.objects.create(
            external_id="m", title="Title", release_date=date(2025, 1, 1), poster_url="https://x/p.jpg"
        )
        summary = summarize(movie)
        self.assertEqual(summary["content_type"], "movie")
        self.assertEqual(summary["title"], "Title")
        self.assertEqual(summary["date"], date(2025, 1, 1))
        self.assertEqual(summary["subtitle"], "Movie")
        self.assertEqual(summary["poster_url"], "https://x/p.jpg")


class GenreFilterTests(TestCase):
    def test_filters_by_genre_membership(self):
        action = Movie.objects.create(external_id="a", title="A", genres=["Action", "Thriller"])
        Movie.objects.create(external_id="b", title="B", genres=["Comedy"])
        filtered = GenreFilterSet({"genre": " Action "}, queryset=Movie.objects.all()).qs
        self.assertEqual(list(filtered), [action])


class CeleryScheduleTests(SimpleTestCase):
    def test_app_is_configured(self):
        self.assertEqual(celery_app.main, "config")

    def test_every_scheduled_task_is_registered(self):
        # Entries are added in the phase that defines the task, so every task the
        # beat schedule references must already be registered. (Empty until Phase 3.)
        for name, config in settings.CELERY_BEAT_SCHEDULE.items():
            self.assertIn(config["task"], celery_app.tasks, f"{name}: {config['task']} is not registered")


class SeedDemoCommandTests(TestCase):
    def test_creates_rows_and_is_idempotent(self):
        from django.core.management import call_command

        from anime.models import Anime
        from sports.models import FootballFixture
        from tv.models import TVShow

        call_command("seed_demo", "--count", "5", verbosity=0)
        self.assertEqual(Movie.objects.filter(external_id__startswith="demo-movie-").count(), 5)
        self.assertEqual(TVShow.objects.filter(external_id__startswith="demo-tv-").count(), 5)
        self.assertEqual(Anime.objects.filter(external_id__startswith="demo-anime-").count(), 5)
        self.assertEqual(Game.objects.filter(external_id__startswith="demo-game-").count(), 5)
        self.assertEqual(FootballFixture.objects.filter(external_id__startswith="demo-fixture-").count(), 5)
        self.assertTrue(Movie.objects.filter(trending_rank__isnull=False).exists())

        call_command("seed_demo", "--count", "5", verbosity=0)  # re-run must not duplicate
        self.assertEqual(Movie.objects.filter(external_id__startswith="demo-movie-").count(), 5)


class SchemaEndpointTests(TestCase):
    def test_schema_and_docs_are_public(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)
