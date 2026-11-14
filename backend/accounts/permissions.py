"""Custom DRF permissions for the accounts domain."""

from rest_framework.permissions import BasePermission


class IsVerifiedUser(BasePermission):
    """Allow only authenticated users who have verified their email.

    Denials return 403 with a machine-readable ``code`` of ``email_not_verified``
    in the body, so the frontend can tell "not verified" apart from other 403s
    and prompt the user to check their inbox. Used by the library in Phase 8.
    """

    code = "email_not_verified"
    message = {
        "detail": "Your email address is not verified.",
        "code": "email_not_verified",
    }

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_email_verified)
