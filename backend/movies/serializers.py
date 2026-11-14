"""Serializers for the public movie endpoints."""

from rest_framework import serializers

from .models import Movie, movie_status
from .services import similar_movies


class MovieListSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id",
            "content_type",
            "title",
            "poster_url",
            "release_date",
            "rating",
            "popularity",
            "genres",
            "trending_rank",
            "status",
        ]

    def get_content_type(self, obj):
        return "movie"

    def get_status(self, obj):
        return movie_status(obj.release_date)


class MovieDetailSerializer(MovieListSerializer):
    similar = serializers.SerializerMethodField()

    class Meta(MovieListSerializer.Meta):
        fields = MovieListSerializer.Meta.fields + [
            "description",
            "backdrop_url",
            "trailer_youtube_key",
            "runtime",
            "cast",
            "production_companies",
            "similar",
        ]

    def get_similar(self, obj):
        return MovieListSerializer(similar_movies(obj), many=True, context=self.context).data
