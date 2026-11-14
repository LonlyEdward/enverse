"""Unit tests for the environment-variable helpers (no database needed)."""

from unittest import mock

from django.test import SimpleTestCase

from config.env import env_bool, env_int, env_list, with_redis_db


class EnvBoolTests(SimpleTestCase):
    def test_unset_returns_default(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertFalse(env_bool("FLAG"))
            self.assertTrue(env_bool("FLAG", default=True))

    def test_truthy_values(self):
        for value in ("1", "true", "TRUE", "Yes", "on", " on "):
            with mock.patch.dict("os.environ", {"FLAG": value}):
                self.assertTrue(env_bool("FLAG"), value)

    def test_falsey_values(self):
        # The whole point: the string "False" must read as False, not True.
        for value in ("0", "false", "False", "no", "off", ""):
            with mock.patch.dict("os.environ", {"FLAG": value}):
                self.assertFalse(env_bool("FLAG", default=True), value)


class EnvIntTests(SimpleTestCase):
    def test_unset_or_empty_returns_default(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(env_int("N", 7), 7)
        with mock.patch.dict("os.environ", {"N": "   "}):
            self.assertEqual(env_int("N", 7), 7)

    def test_parses_value(self):
        with mock.patch.dict("os.environ", {"N": " 42 "}):
            self.assertEqual(env_int("N", 7), 42)


class EnvListTests(SimpleTestCase):
    def test_splits_and_trims_dropping_blanks(self):
        with mock.patch.dict("os.environ", {"HOSTS": " a , b ,, c "}):
            self.assertEqual(env_list("HOSTS"), ["a", "b", "c"])

    def test_default_when_unset(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(env_list("HOSTS"), [])
            self.assertEqual(env_list("HOSTS", "x,y"), ["x", "y"])


class WithRedisDbTests(SimpleTestCase):
    def test_replaces_existing_db(self):
        self.assertEqual(
            with_redis_db("redis://:pw@host:6379/0", 1),
            "redis://:pw@host:6379/1",
        )

    def test_adds_db_when_absent(self):
        self.assertEqual(
            with_redis_db("redis://host:6379", 1),
            "redis://host:6379/1",
        )

    def test_plain_url_without_auth(self):
        self.assertEqual(
            with_redis_db("redis://localhost:6379/0", 2),
            "redis://localhost:6379/2",
        )
