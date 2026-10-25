from django.contrib.postgres.fields import ArrayField
from django.db import models

from content.models import SyncedContent


class Game(SyncedContent):
    release_date = models.DateField(null=True, blank=True, db_index=True)
    previous_release_date = models.DateField(null=True, blank=True)
    platforms = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    rating = models.FloatField(null=True, blank=True)
    screenshots = ArrayField(models.URLField(max_length=500), default=list, blank=True)
    trailer_url = models.URLField(max_length=500, blank=True)

    class Meta:
        ordering = [models.F("release_date").desc(nulls_last=True), "title"]