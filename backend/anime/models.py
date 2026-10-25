from django.db import models

from content.models import SyncedContent


class Anime(SyncedContent):
    class AiringStatus(models.TextChoices):
        NOT_YET_RELEASED = "not_yet_released", "Not Yet Released"
        RELEASING = "releasing", "Releasing"
        FINISHED = "finished", "Finished"
        HIATUS = "hiatus", "Hiatus"
        CANCELLED = "cancelled", "Cancelled"

    class Season(models.TextChoices):
        WINTER = "winter", "Winter"
        SPRING = "spring", "Spring"
        SUMMER = "summer", "Summer"
        FALL = "fall", "Fall"

    airing_status = models.CharField(
        max_length=20, choices=AiringStatus.choices, default=AiringStatus.NOT_YET_RELEASED, db_index=True
    )
    season = models.CharField(max_length=6, choices=Season.choices, blank=True)
    season_year = models.PositiveSmallIntegerField(null=True, blank=True)
    next_airing_episode_number = models.PositiveIntegerField(null=True, blank=True)
    next_airing_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["title"]


class AnimeEpisode(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name="episodes")
    episode_number = models.PositiveIntegerField()
    aired_at = models.DateTimeField(null=True, blank=True)
    notified = models.BooleanField(default=False)

    class Meta:
        ordering = ["anime", "episode_number"]
        constraints = [
            models.UniqueConstraint(fields=["anime", "episode_number"], name="unique_anime_episode_number"),
        ]

    def __str__(self):
        return f"{self.anime.title} - Episode {self.episode_number}"