"""Serializers for the public TV endpoints."""

from rest_framework import serializers

from .models import TVSeason, TVShow


class TVSeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = TVSeason
        fields = ["id", "season_number", "air_date", "state"]


class TVShowListSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = TVShow
        fields = [
            "id",
            "content_type",
            "title",
            "poster_url",
            "status",
            "rating",
            "popularity",
            "genres",
            "first_air_date",
            "next_episode_air_date",
            "trending_rank",
        ]

    def get_content_type(self, obj) -> str:
        return "tv"


class TVShowDetailSerializer(TVShowListSerializer):
    seasons = TVSeasonSerializer(many=True, read_only=True)

    class Meta(TVShowListSerializer.Meta):
        fields = TVShowListSerializer.Meta.fields + [
            "description",
            "backdrop_url",
            "trailer_youtube_key",
            "number_of_seasons",
            "next_episode_season",
            "next_episode_number",
            "seasons",
        ]
