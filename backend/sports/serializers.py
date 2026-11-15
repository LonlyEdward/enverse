"""Serializers for the public football endpoints."""

from rest_framework import serializers

from .models import FootballFixture, FootballTeam


class TeamRefSerializer(serializers.ModelSerializer):
    """The minimal team shape embedded inside a fixture (keeps payloads light)."""

    class Meta:
        model = FootballTeam
        fields = ["id", "name", "logo_url"]


class FootballTeamSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = FootballTeam
        fields = ["id", "content_type", "external_id", "name", "logo_url", "competition"]

    def get_content_type(self, obj) -> str:
        return "football_team"


class FootballFixtureSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()
    home_team = TeamRefSerializer(read_only=True)
    away_team = TeamRefSerializer(read_only=True)

    class Meta:
        model = FootballFixture
        fields = [
            "id",
            "content_type",
            "external_id",
            "competition",
            "league_external_id",
            "round",
            "venue",
            "kickoff_at",
            "status",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
        ]

    def get_content_type(self, obj) -> str:
        return "football_fixture"


class FootballTeamDetailSerializer(FootballTeamSerializer):
    """Team detail with its upcoming fixtures and recent results attached.

    The two fixture lists are supplied by the view (already fetched with the
    teams joined in) via the serializer context, so this adds no queries.
    """

    next_fixtures = serializers.SerializerMethodField()
    recent_results = serializers.SerializerMethodField()

    class Meta(FootballTeamSerializer.Meta):
        fields = FootballTeamSerializer.Meta.fields + ["next_fixtures", "recent_results"]

    def get_next_fixtures(self, obj) -> list:
        return FootballFixtureSerializer(self.context.get("next_fixtures", []), many=True).data

    def get_recent_results(self, obj) -> list:
        return FootballFixtureSerializer(self.context.get("recent_results", []), many=True).data


class CompetitionSerializer(serializers.Serializer):
    """A distinct competition with how many fixtures we currently hold for it."""

    competition = serializers.CharField()
    league_external_id = serializers.IntegerField(allow_null=True)
    fixture_count = serializers.IntegerField()
