from django.contrib import admin

# Register your models here.
from .models import SyncLog


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ("source", "status", "items_processed", "started_at", "finished_at")
    list_filter = ("source", "status")
    readonly_fields = ("started_at",)