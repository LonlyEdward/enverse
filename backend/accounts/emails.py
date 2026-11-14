"""Transactional emails for the accounts flows.

Kept as small standalone functions so they are easy to call from a view today
and easy to move behind a Celery task later without touching the callers. In
development the console email backend prints these to the backend logs.
"""

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import make_email_verification_token


def send_verification_email(user):
    """Email the user a link to verify their address."""
    token = make_email_verification_token(user)
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    send_mail(
        subject="Verify your EnVerse email address",
        message=(
            f"Welcome to EnVerse!\n\n"
            f"Please confirm your email address by opening this link:\n{link}\n\n"
            f"The link expires in 3 days. If you did not create an account, ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(user):
    """Email the user a link to choose a new password.

    The uid is the user's UUID primary key, base64-encoded; the token is bound to
    the user's current password hash, so it stops working once the password
    changes.
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
    send_mail(
        subject="Reset your EnVerse password",
        message=(
            f"We received a request to reset your EnVerse password.\n\n"
            f"Open this link to choose a new one:\n{link}\n\n"
            f"If you did not request this, you can safely ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
