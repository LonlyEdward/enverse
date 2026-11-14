"""Signed, expiring tokens for email verification.

We use ``django.core.signing`` rather than storing a token row: the token is
self-contained (it carries the user id and a timestamp, signed with SECRET_KEY),
so there is nothing to persist or clean up. Password-reset tokens are handled
separately by Django's ``default_token_generator`` (see ``emails.py``).
"""

from django.core import signing

VERIFICATION_SALT = "accounts.email-verification"
VERIFICATION_MAX_AGE = 60 * 60 * 24 * 3  # 3 days, in seconds


def make_email_verification_token(user):
    """Return a signed token that encodes the user's primary key."""
    return signing.dumps(str(user.pk), salt=VERIFICATION_SALT)


def read_email_verification_token(token):
    """Return the user pk from a token, or raise ``signing.BadSignature``.

    ``SignatureExpired`` (a subclass of ``BadSignature``) is raised for tokens
    older than ``VERIFICATION_MAX_AGE``, so callers can treat any bad or expired
    token the same way.
    """
    return signing.loads(token, salt=VERIFICATION_SALT, max_age=VERIFICATION_MAX_AGE)
