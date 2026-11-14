"""Thin client for the RAWG video games API (https://api.rawg.io/api).

The key is sent as the ``key`` query parameter. The free quota is limited, so the
sync keeps per-item detail calls to a small batch per run.
"""

import logging

import requests
from django.conf import settings

from core.http import build_session

logger = logging.getLogger(__name__)


class RAWGError(Exception):
    pass


class RAWGClient:
    BASE_URL = "https://api.rawg.io/api"

    def __init__(self, api_key="", session=None):
        self.api_key = api_key or ""
        self.session = session or build_session()

    @property
    def is_configured(self):
        return bool(self.api_key)

    def _get(self, path, params=None):
        params = dict(params or {})
        params["key"] = self.api_key
        try:
            response = self.session.get(f"{self.BASE_URL}{path}", params=params)
        except requests.RequestException as exc:
            raise RAWGError(f"RAWG request to {path} failed: {exc}") from exc
        if response.status_code != 200:
            raise RAWGError(f"RAWG {path} returned HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise RAWGError(f"RAWG {path} returned a non-JSON body") from exc

    @staticmethod
    def _date_range(dates):
        start, end = dates
        return f"{start.isoformat()},{end.isoformat()}"

    def list_games(self, dates, ordering, page_size=40, page=1):
        return self._get(
            "/games",
            {"dates": self._date_range(dates), "ordering": ordering, "page_size": page_size, "page": page},
        )

    def game_detail(self, game_id):
        return self._get(f"/games/{game_id}")

    def game_screenshots(self, game_id):
        return self._get(f"/games/{game_id}/screenshots")

    def game_movies(self, game_id):
        return self._get(f"/games/{game_id}/movies")


def build_rawg_client():
    return RAWGClient(api_key=settings.RAWG_API_KEY)
