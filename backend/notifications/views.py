"""Notification feed, read actions and per-user preferences. Authenticated only.

The feed is the in-app channel only (email rows are an internal delivery detail).
Every queryset is scoped to ``request.user``, so one user can never read, mark or
delete another user's notifications — a foreign id is simply a 404.
"""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.registry import load_content

from .models import Notification, NotificationPreference
from .serializers import NotificationPreferenceSerializer, NotificationSerializer

TRUTHY = {"1", "true", "yes"}


class NotificationListView(generics.ListAPIView):
    """``GET notifications/?unread=&kind=`` — the user's in-app feed, newest first."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "notifications"
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user, channel=Notification.Channel.IN_APP)
        if (self.request.query_params.get("unread") or "").lower() in TRUTHY:
            qs = qs.filter(read_at__isnull=True)
        kind = self.request.query_params.get("kind")
        if kind:
            qs = qs.filter(kind=kind)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        rows = page if page is not None else list(queryset)
        items = load_content([(row.content_type, row.object_id) for row in rows])
        context = {**self.get_serializer_context(), "items": items}
        data = self.get_serializer(rows, many=True, context=context).data
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "notifications"

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user, channel=Notification.Channel.IN_APP, read_at__isnull=True
        ).count()
        return Response({"count": count})


class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "notifications"

    def post(self, request, pk):
        notification = _own_in_app(request.user).filter(pk=pk).first()
        if notification is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at", "updated_at"])
        return Response({"id": notification.id, "read_at": notification.read_at})


class ReadAllView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "notifications"

    def post(self, request):
        updated = _own_in_app(request.user).filter(read_at__isnull=True).update(read_at=timezone.now())
        return Response({"marked_read": updated})


class NotificationDestroyView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "notifications"

    def get_queryset(self):
        return _own_in_app(self.request.user)


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """``GET``/``PATCH users/me/preferences/notifications/`` — created on first touch."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "notifications"
    serializer_class = NotificationPreferenceSerializer
    http_method_names = ["get", "patch"]

    def get_object(self):
        pref, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return pref


def _own_in_app(user):
    return Notification.objects.filter(user=user, channel=Notification.Channel.IN_APP)
