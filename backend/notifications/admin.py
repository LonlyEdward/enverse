from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "content_type", "object_id", "channel", "created_at", "read_at", "sent_at")
    list_filter = ("kind", "channel", "content_type")
    search_fields = ("user__email", "event_key", "title")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "in_app_enabled", "email_enabled", "notify_releases", "notify_schedules", "notify_updates")
    search_fields = ("user__email",)
