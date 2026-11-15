from django.db import models
from django.utils import timezone

from content.models import SyncedContent


class TVShow(SyncedContent):
    class Status(models.TextChoices):
        RETURNING = "returning", "Returning Series"
        ENDED = "ended", "Ended"
        CANCELED = "canceled", "Canceled"

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RETURNING, db_index=True)
    rating = models.FloatField(null=True, blank=True)
    first_air_date = models.DateField(null=True, blank=True, db_index=True)
    number_of_seasons = models.PositiveIntegerField(null=True, blank=True)
    # The next episode TMDB knows about (all nullable when nothing is scheduled):
    next_episode_air_date = models.DateField(null=True, blank=True, db_index=True)
    next_episode_season = models.PositiveIntegerField(null=True, blank=True)
    next_episode_number = models.PositiveIntegerField(null=True, blank=True)
    backdrop_url = models.URLField(max_length=500, blank=True)
    trailer_youtube_key = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["title"]


def season_state(air_date, season_number, next_episode_season, today=None):
    """Compute a season's state from its air date (never frozen at import).

    - no/future air date  -> announced
    - the next episode belongs to this season -> airing
    - otherwise (air date in the past) -> aired

    ``today`` is passed in by tests; otherwise resolved at call time.
    """
    if today is None:
        today = timezone.localdate()
    if next_episode_season is not None and next_episode_season == season_number:
        return TVSeason.State.AIRING
    if air_date is None or air_date > today:
        return TVSeason.State.ANNOUNCED
    return TVSeason.State.AIRED


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


# Module-level alias so SPECTACULAR_SETTINGS["ENUM_NAME_OVERRIDES"] can name this
# enum (import_string cannot reach a nested TextChoices class).
TVSHOW_STATUS_CHOICES = TVShow.Status.choices