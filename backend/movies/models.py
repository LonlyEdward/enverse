from datetime import timedelta

from django.db import models
from django.utils import timezone

from content.models import SyncedContent

NOW_SHOWING_DAYS = 45
RECENT_DAYS = 90


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
    rating = models.FloatField(null=True, blank=True)
    trailer_youtube_key = models.CharField(max_length=20, blank=True)

    objects = MovieQuerySet.as_manager()

    class Meta:
        ordering = [models.F("release_date").desc(nulls_last=True), "title"]