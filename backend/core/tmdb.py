"""Thin client for The Movie Database (TMDB) v3 API.

Only the endpoints the movie sync needs. The client just fetches and returns raw
JSON; turning that into model fields is the mappers' job (``movies/mappers.py``),
so the parsing stays pure and unit-testable without the network.

Auth (see docs/BUILD_PLAN.md section 2): a v4 read token (starts with ``eyJ``) is
sent as a Bearer header; a classic v3 key is sent as the ``api_key`` query param.
"""

import logging

import requests
from django.conf import settings

from core.http import build_session

logger = logging.getLogger(__name__)


class TMDBError(Exception):
    """Raised for any non-2xx response or transport failure from TMDB."""


class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"
    POSTER_SIZE = "w500"
    BACKDROP_SIZE = "w1280"
    PROFILE_SIZE = "w185"

    def __init__(self, api_key="", session=None):
        self.api_key = api_key or ""
        self.session = session or build_session()

    @property
    def is_configured(self):
        return bool(self.api_key)

    # --- low-level ---------------------------------------------------------

    def _get(self, path, params=None):
        params = dict(params or {})
        headers = {"Accept": "application/json"}
        if self.api_key.startswith("eyJ"):  # v4 read token
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            params["api_key"] = self.api_key
        try:
            response = self.session.get(f"{self.BASE_URL}{path}", params=params, headers=headers)
        except requests.RequestException as exc:
            raise TMDBError(f"TMDB request to {path} failed: {exc}") from exc
        if response.status_code != 200:
            raise TMDBError(f"TMDB {path} returned HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise TMDBError(f"TMDB {path} returned a non-JSON body") from exc

    # --- endpoints ---------------------------------------------------------

    def now_playing(self, page=1):
        return self._get("/movie/now_playing", {"page": page})

    def upcoming(self, page=1):
        return self._get("/movie/upcoming", {"page": page})

    def trending_movies(self):
        return self._get("/trending/movie/week")

    def genre_list(self):
        """Return ``{genre_id: genre_name}`` for mapping list-endpoint genre ids."""
        data = self._get("/genre/movie/list")
        return {g["id"]: g["name"] for g in data.get("genres", []) if "id" in g and g.get("name")}

    def movie_detail(self, movie_id):
        return self._get(f"/movie/{movie_id}", {"append_to_response": "videos,credits"})

    # --- image helpers -----------------------------------------------------

    def _image_url(self, path, size):
        if not path:
            return ""
        return f"{self.IMAGE_BASE_URL}/{size}{path}"

    def poster_url(self, path):
        return self._image_url(path, self.POSTER_SIZE)

    def backdrop_url(self, path):
        return self._image_url(path, self.BACKDROP_SIZE)

    def profile_url(self, path):
        return self._image_url(path, self.PROFILE_SIZE)


def build_tmdb_client():
    """Build a client from the configured key. Call ``.is_configured`` before use."""
    return TMDBClient(api_key=settings.TMDB_API_KEY)
