"""Notification routes (mounted under /api/v1/)."""

from django.urls import path

from . import views

urlpatterns = [
    path("notifications/", views.NotificationListView.as_view(), name="notification-list"),
    path("notifications/unread-count/", views.UnreadCountView.as_view(), name="notification-unread-count"),
    path("notifications/read-all/", views.ReadAllView.as_view(), name="notification-read-all"),
    path("notifications/<int:pk>/read/", views.MarkReadView.as_view(), name="notification-read"),
    path("notifications/<int:pk>/", views.NotificationDestroyView.as_view(), name="notification-detail"),
    path(
        "users/me/preferences/notifications/",
        views.NotificationPreferenceView.as_view(),
        name="notification-preferences",
    ),
]
