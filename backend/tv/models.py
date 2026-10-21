from django.db import models

from content.models import SyncedContent


class TVShow(SyncedContent):
    class Status(models.TextChoices):
        RETURNING = "returning", "Returning Series"
        ENDED = "ended", "Ended"
        CANCELED = "canceled", "Canceled"

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RETURNING, db_index=True)

    class Meta:
        ordering = ["title"]


class TVSeason(models.Model):
    class State(models.TextChoices):
        ANNOUNCED = "announced", "Announced"
        AIRING = "airing", "Airing"
        AIRED = "aired", "Aired"

    show = models.ForeignKey(TVShow, on_delete=models.CASCADE, related_name="seasons")
    season_number = models.PositiveIntegerField()
    air_date = models.DateField(null=True, blank=True, db_index=True)
    state = models.CharField(max_length=10, choices=State.choices, default=State.ANNOUNCED, db_index=True)

    class Meta:
        ordering = ["show", "season_number"]
        constraints = [
            models.UniqueConstraint(fields=["show", "season_number"], name="unique_show_season_number"),
        ]

    def __str__(self):
        return f"{self.show.title} - Season {self.season_number}"