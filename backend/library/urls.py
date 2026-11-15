"""Library routes (mounted under /api/v1/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("library/favorites/", views.FavoriteListCreateView.as_view(), name="favorite-list"),
    path("library/favorites/<int:pk>/", views.FavoriteDestroyView.as_view(), name="favorite-detail"),
    path("library/watchlist/", views.WatchlistListCreateView.as_view(), name="watchlist-list"),
    path("library/watchlist/<int:pk>/", views.WatchlistDestroyView.as_view(), name="watchlist-detail"),
    path("library/bookmarks/", views.BookmarkListCreateView.as_view(), name="bookmark-list"),
    path("library/bookmarks/<int:pk>/", views.BookmarkDestroyView.as_view(), name="bookmark-detail"),
    path("library/following/", views.FollowingListCreateView.as_view(), name="following-list"),
    path("library/following/<int:pk>/", views.FollowingDetailView.as_view(), name="following-detail"),
    path("library/status/", views.LibraryStatusView.as_view(), name="library-status"),
]
