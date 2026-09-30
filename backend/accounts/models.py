from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    display_name = models.CharField(max_length=30, unique=True, blank=True)
    avatar_url = models.URLField(blank=True)
    is_email_verified = models.BooleanField(default=False)
