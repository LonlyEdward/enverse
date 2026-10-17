from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.

class User(AbstractUser):
    display_name = models.CharField(max_length=30, unique=True, blank=True)
    avatar_url = models.URLField(blank=True)
    is_email_verified = models.BooleanField(default=False)


class GenrePreference(models.Model):
    CONTENT_TYPES = [
        ("movie", "Movie"),
        ("tv", "TV"),
        ("anime", "Anime"),
        ("game", "Game"),
        ("football", "Football"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="genre_preferences")

    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES,)

    def __str__(self):
        return f"{self.user} — {self.get_content_type_display()}: {self.genre}"

