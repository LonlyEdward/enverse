"""TV routes (mounted under /api/v1/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("tv/", views.TVListView.as_view(), name="tv-list"),
    path("tv/trending/", views.TVTrendingView.as_view(), name="tv-trending"),
    path("tv/<int:pk>/", views.TVDetailView.as_view(), name="tv-detail"),
    path("tv/<int:pk>/seasons/", views.TVSeasonsView.as_view(), name="tv-seasons"),
]
