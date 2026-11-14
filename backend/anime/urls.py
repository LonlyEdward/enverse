"""Anime routes (mounted under /api/v1/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("anime/", views.AnimeListView.as_view(), name="anime-list"),
    path("anime/trending/", views.AnimeTrendingView.as_view(), name="anime-trending"),
    path("anime/airing/", views.AnimeAiringView.as_view(), name="anime-airing"),
    path("anime/<int:pk>/", views.AnimeDetailView.as_view(), name="anime-detail"),
    path("anime/<int:pk>/episodes/", views.AnimeEpisodesView.as_view(), name="anime-episodes"),
]
