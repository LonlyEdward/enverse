"""Thin client for API-Football v3 (https://v3.football.api-sports.io).

Two quirks drive the design (see docs/BUILD_PLAN.md Phase 7):

- The key is sent in the ``x-apisports-key`` header (the direct api-sports.io
  host, not the RapidAPI gateway which uses a different header).
- The API can answer **HTTP 200 with a non-empty ``errors`` field**: an object
  like ``{"plan": "..."}`` when the free plan rejects a season, or
  ``{"token": "..."}`` for a bad key, or ``{"requests": "..."}`` when the daily
  quota is spent. Success is therefore "2xx *and* empty ``errors``", not just a
  2xx status. Both are turned into :class:`APIFootballError`.
"""

import logging

import requests
from django.conf import settings

from core.http import build_session

logger = logging.getLogger(__name__)


class APIFootballError(Exception):
    """Raised for a transport failure or an API-level ``errors`` response."""


class APIFootballClient:
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self, api_key="", session=None):
        self.api_key = api_key or ""
        self.session = session or build_session()

    @property
    def is_configured(self):
        return bool(self.api_key)

    def _get(self, path, params=None):
        headers = {"x-apisports-key": self.api_key}
        try:
            response = self.session.get(f"{self.BASE_URL}{path}", params=params or {}, headers=headers)
        except requests.RequestException as exc:
            raise APIFootballError(f"API-Football request to {path} failed: {exc}") from exc
        if response.status_code != 200:
            raise APIFootballError(f"API-Football {path} returned HTTP {response.status_code}")
        try:
            body = response.json()
        except ValueError as exc:
            raise APIFootballError(f"API-Football {path} returned a non-JSON body") from exc

        # ``errors`` is [] on success but a dict (or non-empty list) on failure,
        # even with a 200 status. Any truthy value is an error.
        errors = body.get("errors")
        if errors:
            raise APIFootballError(f"API-Football {path} returned errors: {_describe_errors(errors)}")
        return body

    def fixtures(self, *, league, season, date_from, date_to):
        """Return the ``response`` list of fixtures for one league in a date window.

        A league's fixtures for a sub-month window fit in a single page, so no
        pagination is needed here (keeping the request budget to one call each).
        """
        body = self._get(
            "/fixtures",
            {
                "league": league,
                "season": season,
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
                "timezone": "UTC",
            },
        )
        return body.get("response") or []


def _describe_errors(errors):
    """Flatten API-Football's ``errors`` (a dict or a list) into one short string."""
    if isinstance(errors, dict):
        return "; ".join(f"{key}: {value}" for key, value in errors.items())
    if isinstance(errors, list):
        return "; ".join(str(item) for item in errors)
    return str(errors)


def build_apifootball_client():
    return APIFootballClient(api_key=settings.API_FOOTBALL_KEY)
