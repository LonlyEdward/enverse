"""Football routes (mounted under /api/v1/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("football/fixtures/", views.FixtureListView.as_view(), name="fixture-list"),
    path("football/fixtures/<int:pk>/", views.FixtureDetailView.as_view(), name="fixture-detail"),
    path("football/teams/", views.TeamListView.as_view(), name="team-list"),
    path("football/teams/<int:pk>/", views.TeamDetailView.as_view(), name="team-detail"),
    path("football/competitions/", views.CompetitionListView.as_view(), name="competition-list"),
]
