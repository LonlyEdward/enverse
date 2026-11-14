"""Tests for the liveness and readiness endpoints."""

from unittest import mock

from django.test import Client, TestCase, override_settings
from django.urls import reverse


class LivenessTests(TestCase):
    def test_returns_ok(self):
        response = self.client.get(reverse("v1:health-live"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_rejects_post(self):
        response = self.client.post(reverse("v1:health-live"))
        self.assertEqual(response.status_code, 405)


class ReadinessTests(TestCase):
    def test_all_dependencies_healthy(self):
        response = self.client.get(reverse("v1:health-ready"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "checks": {"database": "ok", "cache": "ok"}},
        )

    def test_database_failure_returns_503(self):
        with mock.patch(
            "core.health.connection.cursor",
            side_effect=Exception("SECRET internal database detail"),
        ):
            response = self.client.get(reverse("v1:health-ready"))
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["checks"]["database"], "error")
        self.assertEqual(body["checks"]["cache"], "ok")

    def test_cache_failure_returns_503(self):
        with mock.patch(
            "core.health.cache.set",
            side_effect=Exception("SECRET internal cache detail"),
        ):
            response = self.client.get(reverse("v1:health-ready"))
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["checks"]["cache"], "error")
        self.assertEqual(body["checks"]["database"], "ok")

    def test_response_never_leaks_exception_text(self):
        with mock.patch(
            "core.health.connection.cursor",
            side_effect=Exception("SECRET internal database detail"),
        ):
            response = self.client.get(reverse("v1:health-ready"))
        self.assertNotIn(b"SECRET", response.content)

    def test_rejects_post(self):
        response = self.client.post(reverse("v1:health-ready"))
        self.assertEqual(response.status_code, 405)


@override_settings(
    DEBUG=False,
    SECURE_SSL_REDIRECT=True,
    SECURE_REDIRECT_EXEMPT=[r"^api/v1/health/"],
)
class HealthHttpsExemptionTests(TestCase):
    """Health must answer over plain HTTP even when HTTPS redirect is on,
    because platform health checks do not speak HTTPS."""

    def test_health_is_reachable_over_http(self):
        # Fresh client so SecurityMiddleware is built under the overridden settings.
        client = Client()
        response = client.get(reverse("v1:health-live"))
        self.assertEqual(response.status_code, 200)

    def test_other_urls_are_redirected_to_https(self):
        client = Client()
        response = client.get("/admin/")
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response["Location"].startswith("https://"))
