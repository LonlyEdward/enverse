from django.db import models

# Create your models here.
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class SyncLog(models.Model):
    class Source(models.TextChoices):
        TMDB = "tmdb", "TMDB"
        ANILIST = "anilist", "Anilist"
        RAWG = "rawg", "RAWG"
        API_FOOTBALL = "api_football", "API-Football"

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"

    source = models.CharField(max_length=20, choices=Source.choices)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RUNNING)
    items_processed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

     class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["source", "-started_at"])]

    def __str__(self):
        return f"{self.get_source_display()} sync at {self.started_at:%Y-%m-%d %H:%M} ({self.status})"
