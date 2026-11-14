"""Serializers for the public game endpoints."""

from rest_framework import serializers

from .models import Game


def game_status(release_date, today):
    if release_date is None:
        return "unknown"
    return "upcoming" if release_date > today else "released"


class GameListSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "id",
            "content_type",
            "title",
            "poster_url",
            "release_date",
            "platforms",
            "rating",
            "metacritic",
            "popularity",
            "genres",
            "trending_rank",
            "status",
        ]

    def get_content_type(self, obj):
        return "game"

    def get_status(self, obj):
        from django.utils import timezone

        return game_status(obj.release_date, timezone.localdate())


class GameDetailSerializer(GameListSerializer):
    class Meta(GameListSerializer.Meta):
        fields = GameListSerializer.Meta.fields + [
            "description",
            "developers",
            "screenshots",
            "trailer_url",
            "previous_release_date",
        ]
