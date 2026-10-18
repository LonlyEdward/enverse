from django.db import models


class ContentType(models.TextChoices):
    MOVIE = "movie", "Movie"
    TV = "tv", "TV Show"
    ANIME = "anime", "Anime"
    GAME = "game", "Game"
    FOOTBALL = "football", "Football"