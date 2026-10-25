from django.db import models
from django.db.models import F, Q

from core.models import TimeStampedModel


class FootballTeam(TimeStampedModel):
    external_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    logo_url = models.URLField(max_length=500, blank=True)
    competition = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class FootballFixture(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        FINISHED = "finished", "Finished"

    external_id = models.CharField(max_length=50, unique=True)
    home_team = models.ForeignKey(FootballTeam, on_delete=models.CASCADE, related_name="home_fixtures")
    away_team = models.ForeignKey(FootballTeam, on_delete=models.CASCADE, related_name="away_fixtures")
    competition = models.CharField(max_length=100, blank=True)
    kickoff_at = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    home_score = models.PositiveSmallIntegerField(null=True, blank=True)
    away_score = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["kickoff_at"]
        constraints = [
            models.CheckConstraint(condition=~Q(home_team=F("away_team")), name="fixture_teams_differ"),
        ]

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.kickoff_at:%Y-%m-%d})"