import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from core.choices import ContentType


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class GenrePreference(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="genre_preferences")
    content_type = models.CharField(max_length=10, choices=ContentType.choices)
    genre = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "genre"], name="unique_user_content_type_genre"),
        ]

    def __str__(self):
        return f"{self.user} likes {self.genre} ({self.content_type})"


class PlatformPreference(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="platform_preferences")
    platform = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "platform"], name="unique_user_platform"),
        ]

    def __str__(self):
        return f"{self.user} plays on {self.platform}"