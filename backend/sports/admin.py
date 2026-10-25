from django.contrib import admin

from .models import FootballFixture, FootballTeam


@admin.register(FootballTeam)
class FootballTeamAdmin(admin.ModelAdmin):
    list_display = ("name", "competition")
    search_fields = ("name", "external_id")


@admin.register(FootballFixture)
class FootballFixtureAdmin(admin.ModelAdmin):
    list_display = ("home_team", "away_team", "kickoff_at", "status", "home_score", "away_score")
    list_filter = ("status", "competition")