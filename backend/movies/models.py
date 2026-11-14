from datetime import timedelta

from django.db import models
from django.utils import timezone

from content.models import SyncedContent

NOW_SHOWING_DAYS = 45
RECENT_DAYS = 90


def movie_status(release_date, today=None):
    """Compute a movie's status from its release date (never stored; calendar-dependent).

    ``today`` is passed in only by tests; in normal use it is resolved at call
    time so the status is never frozen at import.
    """
    if release_date is None:
        return "unknown"
    if today is None:
        today = timezone.localdate()
    if release_date > today:
        return "upcoming"
    if release_date >= today - timedelta(days=NOW_SHOWING_DAYS):
        return "now_showing"
    if release_date >= today - timedelta(days=RECENT_DAYS):
        return "recent"
    return "released"


class MovieQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(release_date__gt=timezone.localdate())

    def now_showing(self):
        today = timezone.localdate()
        return self.filter(
            release_date__lte=today,
            release_date__gte=today - timedelta(days=NOW_SHOWING_DAYS),
        )

    def recent(self):
        today = timezone.localdate()
        return self.filter(
            release_date__lte=today,
            release_date__gte=today - timedelta(days=RECENT_DAYS),
        )


class Movie(SyncedContent):
    release_date = models.DateField(null=True, blank=True, db_index=True)
    # When a release date shifts, the sync copies the old value here so Phase 10
    # notifications can detect "date changed" events (games already track this).
    previous_release_date = models.DateField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    trailer_youtube_key = models.CharField(max_length=20, blank=True)

    # Filled by the capped detail rotation (not on every list sync):
    backdrop_url = models.URLField(max_length=500, blank=True)
    runtime = models.PositiveIntegerField(null=True, blank=True)  # minutes
    cast = models.JSONField(default=list, blank=True)  # top ~10 {name, character, profile_url}
    production_companies = models.JSONField(default=list, blank=True)  # [{name, logo_url}]

    objects = MovieQuerySet.as_manager()

    class Meta:
        ordering = [models.F("release_date").desc(nulls_last=True), "title"]