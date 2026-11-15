"""The calendar endpoint: a unified, dated feed across all content types."""

from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services

TRUTHY = {"1", "true", "yes"}


class CalendarView(APIView):
    """``GET calendar/?start=&end=&type=&mine=`` — dated events, span capped at 62 days.

    Public, except ``mine=true`` (the user's own library) which requires a login.
    """

    permission_classes = [AllowAny]
    throttle_scope = "calendar"

    def get(self, request):
        start = parse_date(request.query_params.get("start") or "")
        end = parse_date(request.query_params.get("end") or "")
        if start is None or end is None:
            return self._bad("start and end must be valid YYYY-MM-DD dates.")
        if end < start:
            return self._bad("end must not be before start.")
        if (end - start).days > services.MAX_SPAN_DAYS:
            return self._bad(f"The range must not exceed {services.MAX_SPAN_DAYS} days.")

        type_filter = request.query_params.get("type")
        if type_filter and type_filter not in services.SOURCES:
            return self._bad("Unknown type.")

        mine = (request.query_params.get("mine") or "").lower() in TRUTHY
        if mine and not request.user.is_authenticated:
            raise NotAuthenticated("Log in to see your own calendar.")

        rows = services.build_calendar(start, end, request.user, type_filter=type_filter, mine=mine)
        return Response({"start": start, "end": end, "results": [self._serialize(row) for row in rows]})

    @staticmethod
    def _serialize(row):
        return {
            "content_type": row["content_type"],
            "id": row["id"],
            "title": row["title"],
            "poster_url": row["poster_url"],
            "kind": row["kind"],
            "date": row["date"].isoformat() if row["date"] else None,
            "datetime": row["datetime"].isoformat() if row["datetime"] else None,
        }

    @staticmethod
    def _bad(detail):
        return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
