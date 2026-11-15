"""Recommendation routes (mounted under /api/v1/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("recommendations/", views.RecommendationListView.as_view(), name="recommendation-list"),
    path("recommendations/refresh/", views.RecommendationRefreshView.as_view(), name="recommendation-refresh"),
]
