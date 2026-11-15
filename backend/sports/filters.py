"""Filtering for the football list endpoints."""

from django.db.models import Q
from django_filters import rest_framework as filters

from .models import FootballFixture, FootballTeam


class FootballFixtureFilterSet(filters.FilterSet):
    # ``team`` matches the local team id whether it played at home or away.
    team = filters.NumberFilter(method="filter_team")
    competition = filters.CharFilter(field_name="competition", lookup_expr="iexact")
    status = filters.ChoiceFilter(choices=FootballFixture.Status.choices)
    date_from = filters.DateFilter(field_name="kickoff_at__date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="kickoff_at__date", lookup_expr="lte")

    class Meta:
        model = FootballFixture
        fields = ["team", "competition", "status", "date_from", "date_to"]

    def filter_team(self, queryset, name, value):
        return queryset.filter(Q(home_team_id=value) | Q(away_team_id=value))


class FootballTeamFilterSet(filters.FilterSet):
    competition = filters.CharFilter(field_name="competition", lookup_expr="iexact")

    class Meta:
        model = FootballTeam
        fields = ["competition"]
