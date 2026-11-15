"""Notification storage: one row per (user, event, channel), plus per-user prefs.

A notification is identified by its ``event_key`` (e.g. ``released:movie:12``) and
``channel``. The unique ``(user, event_key, channel)`` constraint is what makes
detection idempotent: re-running it every few minutes inserts with
``ignore_conflicts`` and never duplicates a row.
"""

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.choices import ContentType
from core.models import TimeStampedModel


class Notification(TimeStampedModel):
    class Kind(models.TextChoices):
        RELEASE = "release", "Release"
        SCHEDULE = "schedule", "Schedule"
        UPDATE = "update", "Update"

    class Channel(models.TextChoices):
        IN_APP = "in_app", "In-app"
        EMAIL = "email", "Email"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    object_id = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    channel = models.CharField(max_length=10, choices=Channel.choices)
    event_key = models.CharField(max_length=200, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    # Email rows only: when the digest that carried this row was actually sent.
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "event_key", "channel"], name="uniq_notification_event"),
        ]
        indexes = [models.Index(fields=["user", "-created_at"], name="notification_user_recent")]

    def __str__(self):
        return f"{self.user_id}: {self.event_key} ({self.channel})"


class NotificationPreference(TimeStampedModel):
    """One row per user, created lazily. Absent means "all defaults" (everything on)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preference"
    )
    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    notify_releases = models.BooleanField(default=True)
    notify_schedules = models.BooleanField(default=True)
    notify_updates = models.BooleanField(default=True)
    # Genres the user never wants to hear about (spec 4.15 "do not notify: Horror").
    muted_genres = ArrayField(models.CharField(max_length=50), default=list, blank=True)

    def __str__(self):
        return f"Notification preferences for {self.user_id}"
