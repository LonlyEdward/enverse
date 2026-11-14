"""Tests for the accounts and auth API.

Email uses the in-memory backend so ``mail.outbox`` is populated, and the cache
is cleared between tests so per-scope throttle counters do not leak across tests.
"""

from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import GenrePreference, PlatformPreference

User = get_user_model()

LOCMEM_MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}

STRONG_PASSWORD = "Tr0ub4dour-xyz"


@override_settings(MAILERS=LOCMEM_MAILERS)
class AuthTestBase(APITestCase):
    def setUp(self):
        cache.clear()  # reset DRF throttle counters between tests

    def create_user(self, email="user@example.com", password=STRONG_PASSWORD, verified=True, active=True, **extra):
        user = User(email=email, username=email.split("@")[0] + "-x", is_email_verified=verified, is_active=active, **extra)
        user.set_password(password)
        user.save()
        return user


class RegisterTests(AuthTestBase):
    url = "/api/v1/auth/register/"

    def test_success_creates_user_and_sends_email(self):
        response = self.client.post(self.url, {"email": "New@Example.com", "password": STRONG_PASSWORD})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="new@example.com")  # stored lowercased
        self.assertFalse(user.is_email_verified)
        self.assertTrue(user.username)  # auto-generated
        self.assertTrue(user.check_password(STRONG_PASSWORD))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify-email?token=", mail.outbox[0].body)

    def test_duplicate_email_is_case_insensitive(self):
        self.create_user(email="dupe@example.com")
        response = self.client.post(self.url, {"email": "DUPE@example.com", "password": STRONG_PASSWORD})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_weak_password_is_rejected(self):
        response = self.client.post(self.url, {"email": "weak@example.com", "password": "123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email="weak@example.com").exists())


class LoginTests(AuthTestBase):
    url = "/api/v1/auth/login/"

    def setUp(self):
        super().setUp()
        self.user = self.create_user(email="login@example.com")

    def test_success_returns_tokens_and_user(self):
        response = self.client.post(self.url, {"email": "login@example.com", "password": STRONG_PASSWORD})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "login@example.com")
        self.assertTrue(response.data["user"]["is_email_verified"])

    def test_wrong_password_rejected(self):
        response = self.client.post(self.url, {"email": "login@example.com", "password": "wrong-password"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mixed_case_email_can_log_in(self):
        response = self.client.post(self.url, {"email": "LOGIN@Example.com", "password": STRONG_PASSWORD})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_inactive_user_cannot_log_in(self):
        self.create_user(email="inactive@example.com", active=False)
        response = self.client.post(self.url, {"email": "inactive@example.com", "password": STRONG_PASSWORD})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RefreshAndLogoutTests(AuthTestBase):
    refresh_url = "/api/v1/auth/token/refresh/"
    logout_url = "/api/v1/auth/logout/"

    def setUp(self):
        super().setUp()
        self.user = self.create_user(email="refresh@example.com")
        self.refresh = str(RefreshToken.for_user(self.user))

    def test_refresh_rotates_and_blacklists_old_token(self):
        response = self.client.post(self.refresh_url, {"refresh": self.refresh})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)  # rotation returns a new refresh
        # Reusing the old refresh after rotation must fail (blacklisted).
        reused = self.client.post(self.refresh_url, {"refresh": self.refresh})
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.logout_url, {"refresh": self.refresh})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.client.force_authenticate(None)
        # The blacklisted refresh can no longer be exchanged.
        after = self.client.post(self.refresh_url, {"refresh": self.refresh})
        self.assertEqual(after.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self):
        response = self.client.post(self.logout_url, {"refresh": self.refresh})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EmailVerificationTests(AuthTestBase):
    url = "/api/v1/auth/verify-email/"

    def setUp(self):
        super().setUp()
        self.user = self.create_user(email="verify@example.com", verified=False)

    def _token(self):
        from accounts.tokens import make_email_verification_token

        return make_email_verification_token(self.user)

    def test_good_token_verifies(self):
        response = self.client.post(self.url, {"token": self._token()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_tampered_token_rejected(self):
        response = self.client.post(self.url, {"token": self._token() + "tampered"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)

    def test_expired_token_rejected(self):
        token = self._token()
        with mock.patch("accounts.tokens.VERIFICATION_MAX_AGE", -1):
            response = self.client.post(self.url, {"token": token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)


class PasswordResetTests(AuthTestBase):
    request_url = "/api/v1/auth/password-reset/"
    confirm_url = "/api/v1/auth/password-reset/confirm/"

    def setUp(self):
        super().setUp()
        self.user = self.create_user(email="reset@example.com")

    def test_existing_and_unknown_email_give_the_same_response(self):
        existing = self.client.post(self.request_url, {"email": "reset@example.com"})
        unknown = self.client.post(self.request_url, {"email": "nobody@example.com"})
        self.assertEqual(existing.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown.status_code, status.HTTP_200_OK)
        self.assertEqual(existing.data, unknown.data)
        # But only the real account actually receives an email.
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset@example.com", mail.outbox[0].to)

    def _uid_and_token(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        return urlsafe_base64_encode(force_bytes(self.user.pk)), default_token_generator.make_token(self.user)

    def test_confirm_sets_new_password_without_logging_in(self):
        uid, token = self._uid_and_token()
        new_password = "Brand-New-Pass99"
        response = self.client.post(self.confirm_url, {"uid": uid, "token": token, "new_password": new_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("access", response.data)  # reset must not log the user in
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_token_cannot_be_reused_after_password_change(self):
        uid, token = self._uid_and_token()
        first = self.client.post(self.confirm_url, {"uid": uid, "token": token, "new_password": "Brand-New-Pass99"})
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        # The same token no longer validates because the password hash changed.
        second = self.client.post(self.confirm_url, {"uid": uid, "token": token, "new_password": "Another-Pass-77"})
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)


class UserMeTests(AuthTestBase):
    url = "/api/v1/users/me/"

    def setUp(self):
        super().setUp()
        self.user = self.create_user(email="me@example.com", display_name="Original")

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "me@example.com")

    def test_patch_updates_profile_but_not_email(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            self.url,
            {"display_name": "Updated", "avatar_url": "https://example.com/a.png", "email": "hacker@example.com"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Updated")
        self.assertEqual(self.user.email, "me@example.com")  # unchanged


class GenrePreferenceTests(AuthTestBase):
    url = "/api/v1/users/me/preferences/genres/"

    def setUp(self):
        super().setUp()
        self.user = self.create_user(email="genres@example.com")
        self.client.force_authenticate(self.user)

    def test_put_replaces_and_get_returns(self):
        payload = {"items": [
            {"content_type": "movie", "genre": "Action"},
            {"content_type": "anime", "genre": "Shounen"},
        ]}
        response = self.client.put(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.genre_preferences.count(), 2)
        # A second PUT replaces, not appends.
        response = self.client.put(self.url, {"items": [{"content_type": "movie", "genre": "Comedy"}]}, format="json")
        self.assertEqual(self.user.genre_preferences.count(), 1)
        self.assertEqual(response.data["items"], [{"content_type": "movie", "genre": "Comedy"}])

    def test_football_content_type_is_rejected(self):
        response = self.client.put(self.url, {"items": [{"content_type": "football", "genre": "x"}]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_content_type_is_rejected(self):
        response = self.client.put(self.url, {"items": [{"content_type": "podcast", "genre": "x"}]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicates_are_collapsed(self):
        payload = {"items": [
            {"content_type": "movie", "genre": "Action"},
            {"content_type": "movie", "genre": "action"},  # same, different case
        ]}
        self.client.put(self.url, payload, format="json")
        self.assertEqual(self.user.genre_preferences.count(), 1)

    def test_other_users_preferences_are_not_visible(self):
        other = self.create_user(email="other@example.com")
        GenrePreference.objects.create(user=other, content_type="movie", genre="Horror")
        response = self.client.get(self.url)
        self.assertEqual(response.data["items"], [])


class PlatformPreferenceTests(AuthTestBase):
    url = "/api/v1/users/me/preferences/platforms/"

    def setUp(self):
        super().setUp()
        self.user = self.create_user(email="platforms@example.com")
        self.client.force_authenticate(self.user)

    def test_put_replaces_and_dedupes(self):
        response = self.client.put(self.url, {"platforms": ["PC", "PS5", "pc"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(sorted(response.data["platforms"]), ["PC", "PS5"])

    def test_other_users_platforms_not_visible(self):
        other = self.create_user(email="other2@example.com")
        PlatformPreference.objects.create(user=other, platform="Xbox")
        response = self.client.get(self.url)
        self.assertEqual(response.data["platforms"], [])


class ThrottleTests(AuthTestBase):
    url = "/api/v1/auth/register/"

    def test_register_is_throttled(self):
        # register scope is 5/hour; the sixth request in the window is rejected.
        last_status = None
        for i in range(6):
            last_status = self.client.post(
                self.url, {"email": f"t{i}@example.com", "password": STRONG_PASSWORD}
            ).status_code
        self.assertEqual(last_status, status.HTTP_429_TOO_MANY_REQUESTS)
