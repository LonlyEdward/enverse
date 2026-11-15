from django.contrib import admin

from .models import Bookmark, Favorite, Following, WatchlistItem


@admin.register(Favorite, WatchlistItem, Bookmark)
class LibraryEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "content_type", "object_id", "created_at")
    list_filter = ("content_type",)
    search_fields = ("user__email",)


@admin.register(Following)
class FollowingAdmin(admin.ModelAdmin):
    list_display = ("user", "content_type", "object_id", "notifications_enabled", "created_at")
    list_filter = ("content_type", "notifications_enabled")
    search_fields = ("user__email",)
