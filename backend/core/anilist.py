"""Client for the AniList GraphQL API (https://graphql.anilist.co, no key).

Two things bite people here (see docs/BUILD_PLAN.md):
- always send values as GraphQL *variables*, never string-formatted into the
  query;
- AniList can return **HTTP 200 with an ``errors`` array**, so success is not just
  a 2xx status. Both are handled below.
"""

import logging

import requests

from core.http import build_session

logger = logging.getLogger(__name__)

ANILIST_URL = "https://graphql.anilist.co"

# Fields requested for every anime. description(asHtml:false) still yields minor
# markup (<br>), which we keep as-is.
_MEDIA_FIELDS = """
      id
      title { romaji english native }
      description(asHtml: false)
      coverImage { large }
      bannerImage
      genres
      averageScore
      popularity
      status
      season
      seasonYear
      episodes
      studios { nodes { name } }
      nextAiringEpisode { airingAt episode }
"""

PAGE_QUERY = """
query ($page: Int, $perPage: Int, $season: MediaSeason, $seasonYear: Int, $status: MediaStatus, $sort: [MediaSort]) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage currentPage }
    media(type: ANIME, season: $season, seasonYear: $seasonYear, status: $status, sort: $sort) {
%s
    }
  }
}
""" % _MEDIA_FIELDS


class AniListError(Exception):
    """Raised for a transport failure or a GraphQL ``errors`` response."""


class AniListClient:
    # AniList needs no API key, so it is always "configured".
    is_configured = True

    def __init__(self, session=None):
        self.session = session or build_session()

    def query(self, query, variables):
        try:
            response = self.session.post(ANILIST_URL, json={"query": query, "variables": variables})
        except requests.RequestException as exc:
            raise AniListError(f"AniList request failed: {exc}") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise AniListError(f"AniList returned a non-JSON body (HTTP {response.status_code})") from exc
        if body.get("errors"):
            first = body["errors"][0]
            raise AniListError(f"AniList GraphQL error: {first.get('message', first)}")
        if response.status_code != 200:
            raise AniListError(f"AniList returned HTTP {response.status_code}")
        return body.get("data") or {}

    def fetch_media_page(self, *, status=None, season=None, season_year=None, sort=None, page=1, per_page=50):
        """Return the ``media`` list for one page. Only non-None filters are sent."""
        variables = {"page": page, "perPage": per_page}
        if status:
            variables["status"] = status
        if season:
            variables["season"] = season
        if season_year:
            variables["seasonYear"] = season_year
        if sort:
            variables["sort"] = sort
        data = self.query(PAGE_QUERY, variables)
        return (data.get("Page") or {}).get("media") or []


def build_anilist_client():
    return AniListClient()
