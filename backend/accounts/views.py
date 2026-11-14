"""Views for registration, authentication, email verification, password reset,
the current-user profile, and genre/platform preferences.

Thin views: input validation and the real work live in the serializers and in
``emails.py``. Public endpoints set ``AllowAny`` explicitly because the project
default permission is ``IsAuthenticated``.
"""

from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import send_password_reset_email, send_verification_email
from .serializers import (
    GenrePreferencesSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PlatformPreferencesSerializer,
    RegisterSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)

User = get_user_model()


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_verification_email(user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = _tokens_for_user(user)
        return Response({**tokens, "user": UserSerializer(user).data})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            # Already expired/blacklisted/invalid: logging out is idempotent.
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Email verified."})


class ResendVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "resend_verification"

    def post(self, request):
        if not request.user.is_email_verified:
            send_verification_email(request.user)
        # Same response whether or not we actually sent, to avoid leaking state.
        return Response({"detail": "If your email is unverified, a new link has been sent."})


class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        # Only active users get an email, but the response is identical either way
        # so an attacker cannot tell which addresses have accounts.
        user = User.objects.filter(email=email, is_active=True).first()
        if user is not None:
            send_password_reset_email(user)
        return Response({"detail": "If an account exists for this email, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # Deliberately does NOT log the user in.
        return Response({"detail": "Password has been reset."})


class UserMeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "head", "options"]  # no PUT: partial profile edits only

    def get_object(self):
        return self.request.user


class GenrePreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = [
            {"content_type": p.content_type, "genre": p.genre}
            for p in request.user.genre_preferences.all()
        ]
        return Response({"items": items})

    def put(self, request):
        serializer = GenrePreferencesSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get(request)


class PlatformPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        platforms = list(request.user.platform_preferences.values_list("platform", flat=True))
        return Response({"platforms": platforms})

    def put(self, request):
        serializer = PlatformPreferencesSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.get(request)
