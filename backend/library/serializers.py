"""Serializers for the library endpoints.

A read serializer embeds a small ``item`` summary of the referenced content. The
view bulk-resolves those items with ``load_content`` and passes them in via the
``items`` context, so rendering a page never issues a query per row.
"""

from rest_framework import serializers

from core.registry import LIBRARY_CONTENT_TYPES, content_exists, summarize


class LibraryWriteSerializer(serializers.Serializer):
    """Validates a POST body of ``{content_type, object_id}``."""

    content_type = serializers.ChoiceField(choices=LIBRARY_CONTENT_TYPES)
    object_id = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        if not content_exists(attrs["content_type"], attrs["object_id"]):
            raise serializers.ValidationError(
                {"object_id": "No item of that content type with this id exists."}
            )
        return attrs


class WatchlistWriteSerializer(LibraryWriteSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        # You follow teams and fixtures; you do not "watch later" them.
        if attrs["content_type"] == "football":
            raise serializers.ValidationError(
                {"content_type": "Football cannot be added to the watchlist."}
            )
        return attrs


class LibraryItemSerializer(serializers.Serializer):
    """Read shape for a saved item, with the resolved content summary attached."""

    id = serializers.IntegerField(read_only=True)
    content_type = serializers.CharField(read_only=True)
    object_id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    item = serializers.SerializerMethodField()

    def get_item(self, obj):
        items = self.context.get("items", {})
        content = items.get((obj.content_type, obj.object_id))
        # The content row can be absent (e.g. deleted after being saved); the
        # frontend renders a graceful placeholder for a null item.
        return summarize(content) if content is not None else None


class FollowingSerializer(LibraryItemSerializer):
    notifications_enabled = serializers.BooleanField(read_only=True)


class FollowingUpdateSerializer(serializers.Serializer):
    """PATCH body for a following row: only ``notifications_enabled`` may change."""

    notifications_enabled = serializers.BooleanField()
