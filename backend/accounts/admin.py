from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import GenrePreference, PlatformPreference, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "username", "is_email_verified", "is_staff")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("EnVerse profile", {"fields": ("display_name", "avatar_url", "is_email_verified")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (None, {"fields": ("email",)}),
    )


admin.site.register(GenrePreference)
admin.site.register(PlatformPreference)