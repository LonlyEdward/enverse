from django.contrib import admin

from .models import TVSeason, TVShow


class TVSeasonInline(admin.TabularInline):
    model = TVSeason
    extra = 0


@admin.register(TVShow)
class TVShowAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "last_synced_at")
    search_fields = ("title", "external_id")
    list_filter = ("status",)
    inlines = [TVSeasonInline]


@admin.register(TVSeason)
class TVSeasonAdmin(admin.ModelAdmin):
    list_display = ("show", "season_number", "air_date", "state")
    list_filter = ("state",)
    search_fields = ("show__title",)