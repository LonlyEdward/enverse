"""Precomputed per-user recommendations. The API only reads these; a task (or a
lazy first request) writes them."""

from django.conf import settings
from django.db import models

from core.choices import ContentType
from core.models import TimeStampedModel


class Recommendation(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations")
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    object_id = models.PositiveIntegerField()
    score = models.FloatField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-score"]
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="uniq_recommendation"),
        ]
        indexes = [models.Index(fields=["user", "-score"], name="recommendation_user_score")]

    def __str__(self):
        return f"{self.user_id}: {self.content_type}#{self.object_id} ({self.score:.2f})"
