from django.db import models
from django.contrib.postgres.fields import ArrayField


# Create your models here.
from core.models import TimeStampedModel


class SyncedContent(TimeStampedModel):
    external_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    poster_url = models.URLField(max_length=500, blank=True)
    genres = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    # Populated by the sync layer (Phase 2+):
    # popularity drives default ordering and "similar" tie-breaks; trending_rank is
    # assigned 1..N by replace_trending_ranks each run; details_synced_at rotates
    # the expensive per-item detail calls (NULLs first, then oldest).
    popularity = models.FloatField(null=True, blank=True, db_index=True)
    trending_rank = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    details_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title