"""Serializer for a stored recommendation, with the item summary embedded."""

from rest_framework import serializers

from core.registry import summarize

from .models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = ["content_type", "object_id", "score", "reason", "item"]

    def get_item(self, obj) -> "dict | None":
        content = self.context.get("items", {}).get((obj.content_type, obj.object_id))
        return summarize(content) if content is not None else None
