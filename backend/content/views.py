"""Public discovery endpoints: search, trending and genre metadata."""

from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.registry import CONTENT_TYPES
from sports.serializers import FootballFixtureSerializer

from . import services

GENRES_CACHE_SECONDS = 600  # 10 minutes; genres change only when a sync adds one


class SearchView(APIView):
    """``GET search/?q=&type=`` — unified search over titles and team names.

    ``q`` must be at least two characters, so the endpoint never runs an unbounded
    scan. ``type`` optionally narrows to one content type.
    """

    permission_classes = [AllowAny]
    throttle_scope = "search"

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        if len(query) < services.MIN_QUERY_LENGTH:
            return Response(
                {"detail": f"Query must be at least {services.MIN_QUERY_LENGTH} characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        type_filter = request.query_params.get("type")
        if type_filter and type_filter not in services.SEARCH_TYPES:
            return Response({"detail": "Unknown type."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"query": query, "results": services.search(query, type_filter)})


class TrendingView(APIView):
    """``GET trending/`` — top items per content type plus upcoming fixtures."""

    permission_classes = [AllowAny]

    def get(self, request):
        sections, fixtures = services.trending()
        sections["football"] = FootballFixtureSerializer(fixtures, many=True).data
        return Response(sections)


class GenresView(APIView):
    """``GET meta/genres/?type=`` — distinct genres per content type, cached 10 min.

    Football has no genres, so only the four content types are valid; an unknown or
    football ``type`` is a 400.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        type_filter = request.query_params.get("type")
        if type_filter and type_filter not in CONTENT_TYPES:
            return Response({"detail": "Unknown type."}, status=status.HTTP_400_BAD_REQUEST)
        types = [type_filter] if type_filter else CONTENT_TYPES
        return Response({content_type: self._genres_for(content_type) for content_type in types})

    def _genres_for(self, content_type):
        cache_key = f"meta:genres:{content_type}"
        genres = cache.get(cache_key)
        if genres is None:
            genres = services.distinct_genres(content_type)
            cache.set(cache_key, genres, GENRES_CACHE_SECONDS)
        return genres
