"""Public read endpoints for football fixtures, teams and competitions."""

from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import FootballFixtureFilterSet, FootballTeamFilterSet
from .models import FootballFixture, FootballTeam
from .serializers import (
    CompetitionSerializer,
    FootballFixtureSerializer,
    FootballTeamDetailSerializer,
    FootballTeamSerializer,
)

# How many fixtures to attach on each side of a team's detail page.
TEAM_FIXTURE_LIMIT = 10
# Statuses that count as "still to come" for the upcoming-fixtures list.
UPCOMING_STATUSES = [FootballFixture.Status.SCHEDULED, FootballFixture.Status.LIVE]


class FixtureListView(generics.ListAPIView):
    queryset = FootballFixture.objects.select_related("home_team", "away_team")
    serializer_class = FootballFixtureSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = FootballFixtureFilterSet
    ordering_fields = ["kickoff_at", "status"]
    ordering = ["kickoff_at"]


class FixtureDetailView(generics.RetrieveAPIView):
    queryset = FootballFixture.objects.select_related("home_team", "away_team")
    serializer_class = FootballFixtureSerializer
    permission_classes = [AllowAny]


class TeamListView(generics.ListAPIView):
    queryset = FootballTeam.objects.all()
    serializer_class = FootballTeamSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FootballTeamFilterSet
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]


class TeamDetailView(generics.RetrieveAPIView):
    queryset = FootballTeam.objects.all()
    serializer_class = FootballTeamDetailSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        team = self.get_object()
        now = timezone.now()
        played_by = Q(home_team=team) | Q(away_team=team)
        fixtures = FootballFixture.objects.select_related("home_team", "away_team").filter(played_by)
        context["next_fixtures"] = list(
            fixtures.filter(kickoff_at__gte=now, status__in=UPCOMING_STATUSES).order_by("kickoff_at")[
                :TEAM_FIXTURE_LIMIT
            ]
        )
        context["recent_results"] = list(
            fixtures.filter(status=FootballFixture.Status.FINISHED).order_by("-kickoff_at")[
                :TEAM_FIXTURE_LIMIT
            ]
        )
        return context


class CompetitionListView(APIView):
    """Distinct competitions we hold fixtures for, each with a fixture count."""

    permission_classes = [AllowAny]

    def get(self, request):
        rows = (
            FootballFixture.objects.values("competition", "league_external_id")
            .annotate(fixture_count=Count("id"))
            .order_by("competition")
        )
        return Response(CompetitionSerializer(rows, many=True).data)
