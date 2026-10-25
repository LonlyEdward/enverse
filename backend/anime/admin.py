from django.contrib import admin

from .models import Anime, AnimeEpisode


@admin.register(Anime)
class AnimeAdmin(admin.ModelAdmin):
    list_display = ("title", "airing_status", "next_airing_episode_number", "next_airing_at")
    search_fields = ("title", "external_id")
    list_filter = ("airing_status", "season", "season_year")


@admin.register(AnimeEpisode)
class AnimeEpisodeAdmin(admin.ModelAdmin):
    list_display = ("anime", "episode_number", "aired_at", "notified")
    list_filter = ("notified",)