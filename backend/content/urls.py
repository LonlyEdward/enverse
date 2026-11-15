"""Discovery routes (mounted under /api/v1/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.SearchView.as_view(), name="search"),
    path("trending/", views.TrendingView.as_view(), name="trending"),
    path("meta/genres/", views.GenresView.as_view(), name="meta-genres"),
]
