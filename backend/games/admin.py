from django.contrib import admin

from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("title", "release_date", "rating", "last_synced_at")
    search_fields = ("title", "external_id")
    list_filter = ("release_date",)