"""Serializers for registration, authentication and profile/preferences."""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from core.choices import ContentType

from .models import GenrePreference, PlatformPreference
from .tokens import read_email_verification_token

User = get_user_model()

# Genres can be set for these content types; football is excluded (you follow
# teams, not football "genres").
GENRE_CONTENT_TYPES = {
    ContentType.MOVIE,
    ContentType.TV,
    ContentType.ANIME,
    ContentType.GAME,
}


def _generate_unique_username(email):
    """Build a unique username from the email local part plus a random suffix.

    The client never sends a username, but the model still requires a unique one.
    We sanitise the local part to the characters Django's username validator
    allows and append a short random suffix, retrying on the rare collision.
    """
    base = "".join(ch for ch in email.split("@", 1)[0] if ch.isalnum() or ch in "._-")
    base = base or "user"
    for _ in range(10):
        candidate = f"{base}-{get_random_string(6)}"[:150]
        if not User.objects.filter(username=candidate).exists():
            return candidate
    # Astronomically unlikely; fail loudly rather than loop forever.
    raise serializers.ValidationError("Could not generate a unique username.")


class UserSerializer(serializers.ModelSerializer):
    """Public representation of a user. Email is read-only here (changing it
    would need re-verification, which is out of scope for this endpoint)."""

    class Meta:
        model = User
        fields = ("id", "email", "display_name", "avatar_url", "is_email_verified")
        read_only_fields = ("id", "email", "is_email_verified")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("email", "password", "display_name")
        extra_kwargs = {"display_name": {"required": False, "allow_blank": True}}

    def validate_email(self, value):
        # The model lowercases email on save, so compare against the lowercased
        # form to make duplicate detection case-insensitive.
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data["email"]
        user = User(
            email=email,
            username=_generate_unique_username(email),
            display_name=validated_data.get("display_name", ""),
        )
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        # Lowercase so people who typed capitals can still log in (emails are
        # stored lowercased). authenticate() returns None for a wrong password
        # and for inactive users, which is exactly what we want.
        email = attrs["email"].lower()
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        try:
            user_pk = read_email_verification_token(value)
        except signing.BadSignature:
            # Covers both tampered and expired tokens; stay generic on purpose.
            raise serializers.ValidationError("This verification link is invalid or has expired.")
        try:
            self.user = User.objects.get(pk=user_pk)
        except (User.DoesNotExist, ValueError):
            raise serializers.ValidationError("This verification link is invalid or has expired.")
        return value

    def save(self, **kwargs):
        if not self.user.is_email_verified:
            self.user.is_email_verified = True
            self.user.save(update_fields=["is_email_verified"])
        return self.user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        generic_error = serializers.ValidationError(
            {"token": "This password reset link is invalid or has expired."}
        )
        try:
            user_pk = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_pk)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise generic_error
        if not default_token_generator.check_token(user, attrs["token"]):
            raise generic_error
        # Validate the new password against Django's validators, with the user in
        # context so similarity checks work.
        validate_password(attrs["new_password"], user=user)
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class GenrePreferenceItemSerializer(serializers.Serializer):
    content_type = serializers.ChoiceField(choices=sorted(GENRE_CONTENT_TYPES))
    genre = serializers.CharField(max_length=50)

    def validate_genre(self, value):
        normalized = " ".join(value.split())  # trim and collapse internal whitespace
        if not normalized:
            raise serializers.ValidationError("Genre cannot be blank.")
        return normalized


class GenrePreferencesSerializer(serializers.Serializer):
    """Read and fully replace a user's genre preferences in one request."""

    items = GenrePreferenceItemSerializer(many=True)

    @transaction.atomic
    def save(self, **kwargs):
        user = self.context["request"].user
        # De-duplicate (content_type, genre) case-insensitively, keeping first seen.
        seen = set()
        rows = []
        for item in self.validated_data["items"]:
            key = (item["content_type"], item["genre"].casefold())
            if key in seen:
                continue
            seen.add(key)
            rows.append(GenrePreference(user=user, content_type=item["content_type"], genre=item["genre"]))
        # PUT replaces the whole set.
        user.genre_preferences.all().delete()
        GenrePreference.objects.bulk_create(rows)
        return rows


class PlatformPreferencesSerializer(serializers.Serializer):
    """Read and fully replace a user's platform preferences in one request."""

    platforms = serializers.ListField(child=serializers.CharField(max_length=50))

    def validate_platforms(self, value):
        normalized = []
        seen = set()
        for platform in value:
            cleaned = " ".join(platform.split())
            if not cleaned:
                continue
            key = cleaned.casefold()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(cleaned)
        return normalized

    @transaction.atomic
    def save(self, **kwargs):
        user = self.context["request"].user
        rows = [PlatformPreference(user=user, platform=p) for p in self.validated_data["platforms"]]
        user.platform_preferences.all().delete()
        PlatformPreference.objects.bulk_create(rows)
        return rows
