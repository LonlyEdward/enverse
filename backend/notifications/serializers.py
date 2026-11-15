"""Serializers for the notification feed and the per-user preferences."""

from rest_framework import serializers

from core.registry import summarize

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()
    item = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "kind",
            "content_type",
            "object_id",
            "title",
            "body",
            "created_at",
            "read_at",
            "is_read",
            "item",
        ]

    def get_is_read(self, obj):
        return obj.read_at is not None

    def get_item(self, obj):
        content = self.context.get("items", {}).get((obj.content_type, obj.object_id))
        return summarize(content) if content is not None else None


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "in_app_enabled",
            "email_enabled",
            "notify_releases",
            "notify_schedules",
            "notify_updates",
            "muted_genres",
        ]

    def validate_muted_genres(self, value):
        # Normalise to trimmed, de-duplicated, non-empty strings.
        seen = {}
        for genre in value:
            cleaned = genre.strip()
            if cleaned:
                seen.setdefault(cleaned.lower(), cleaned)
        return list(seen.values())
