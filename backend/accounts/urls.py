"""Account, auth and preference routes (mounted under /api/v1/)."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # Auth
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path("auth/resend-verification/", views.ResendVerificationView.as_view(), name="resend-verification"),
    path("auth/password-reset/", views.PasswordResetView.as_view(), name="password-reset"),
    path("auth/password-reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    # Current user
    path("users/me/", views.UserMeView.as_view(), name="user-me"),
    path("users/me/preferences/genres/", views.GenrePreferencesView.as_view(), name="user-genres"),
    path("users/me/preferences/platforms/", views.PlatformPreferencesView.as_view(), name="user-platforms"),
]
