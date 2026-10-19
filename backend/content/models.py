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

    class Meta:
        abstract = True

    def __str__(self):
        return self.title