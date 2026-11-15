from django.contrib import admin

from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("user", "content_type", "object_id", "score", "reason")
    list_filter = ("content_type",)
    search_fields = ("user__email", "reason")
