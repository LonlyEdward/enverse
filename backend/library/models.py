"""The personal library: one small table per kind of saved item.

Each row pins a user to one content item by ``(content_type, object_id)`` where
``object_id`` is the item's **local** row id (our pk), resolved through
``core.registry``. We deliberately avoid a generic foreign key: a string plus an
id is simpler to query, migrate and reason about, and the registry already knows
how to turn the pair back into a model. Because ids collide across tables, an item
is only ever meaningful together with its content type.
"""

from django.conf import settings
from django.db import models

from core.choices import ContentType
from core.models import TimeStampedModel


class LibraryEntry(TimeStampedModel):
    """Shared shape for every library table. Abstract: it creates no table itself.

    The unique constraint and the ``(user, -created_at)`` index are declared on
    each concrete model below, because a named constraint/index on an abstract
    Meta would collide across the subclasses that share it.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="%(class)ss"
    )
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    object_id = models.PositiveIntegerField()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id}: {self.content_type}#{self.object_id}"


class Favorite(LibraryEntry):
    class Meta(LibraryEntry.Meta):
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="uniq_favorite")
        ]
        indexes = [models.Index(fields=["user", "-created_at"], name="favorite_user_recent")]


class WatchlistItem(LibraryEntry):
    class Meta(LibraryEntry.Meta):
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="uniq_watchlist")
        ]
        indexes = [models.Index(fields=["user", "-created_at"], name="watchlist_user_recent")]


class Bookmark(LibraryEntry):
    class Meta(LibraryEntry.Meta):
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="uniq_bookmark")
        ]
        indexes = [models.Index(fields=["user", "-created_at"], name="bookmark_user_recent")]


class Following(LibraryEntry):
    # Per-item mute switch: a user can follow a team/show but silence its
    # notifications without un-following (spec 4.15).
    notifications_enabled = models.BooleanField(default=True)

    class Meta(LibraryEntry.Meta):
        constraints = [
            models.UniqueConstraint(fields=["user", "content_type", "object_id"], name="uniq_following")
        ]
        indexes = [models.Index(fields=["user", "-created_at"], name="following_user_recent")]
