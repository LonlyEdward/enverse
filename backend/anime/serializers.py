"""Serializers for the public anime endpoints."""

from rest_framework import serializers

from .models import Anime, AnimeEpisode


class AnimeEpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimeEpisode
        fields = ["episode_number", "aired_at"]


class AnimeListSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = Anime
        fields = [
            "id",
            "content_type",
            "title",
            "poster_url",
            "airing_status",
            "season",
            "season_year",
            "rating",
            "popularity",
            "genres",
            "studios",
            "next_airing_episode_number",
            "next_airing_at",
            "trending_rank",
        ]

    def get_content_type(self, obj) -> str:
        return "anime"


class AnimeDetailSerializer(AnimeListSerializer):
    episodes = AnimeEpisodeSerializer(many=True, read_only=True)

    class Meta(AnimeListSerializer.Meta):
        fields = AnimeListSerializer.Meta.fields + [
            "description",
            "banner_url",
            "episodes_total",
            "episodes",
        ]
