"""Game routes (mounted under /api/v1/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("games/", views.GameListView.as_view(), name="game-list"),
    path("games/trending/", views.GameTrendingView.as_view(), name="game-trending"),
    path("games/<int:pk>/", views.GameDetailView.as_view(), name="game-detail"),
]
