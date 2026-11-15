"""Library endpoints. Verified users only; each user sees only their own rows.

Every list embeds a content summary per row without an N+1: the page's rows are
resolved in one pass by ``load_content`` (one query per content type, not per
row) and handed to the serializer through context.
"""

from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsVerifiedUser
from core.registry import LIBRARY_CONTENT_TYPES, load_content

from .models import Bookmark, Favorite, Following, WatchlistItem
from .serializers import (
    FollowingSerializer,
    FollowingUpdateSerializer,
    LibraryItemSerializer,
    LibraryWriteSerializer,
    WatchlistWriteSerializer,
)


def _items_for(rows):
    """One bulk lookup of the content each row points at, keyed for the serializer."""
    return load_content([(row.content_type, row.object_id) for row in rows])


class LibraryListCreateView(generics.ListCreateAPIView):
    """GET a user's rows of one kind (optionally filtered by content_type) and
    POST a new one. POST is idempotent: 201 when created, 200 when it existed.
    """

    permission_classes = [IsVerifiedUser]
    throttle_scope = "library"
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at"]

    model = None
    read_serializer_class = LibraryItemSerializer
    write_serializer_class = LibraryWriteSerializer

    def get_queryset(self):
        qs = self.model.objects.filter(user=self.request.user)
        content_type = self.request.query_params.get("content_type")
        if content_type:
            qs = qs.filter(content_type=content_type)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        rows = page if page is not None else list(queryset)
        context = {**self.get_serializer_context(), "items": _items_for(rows)}
        data = self.read_serializer_class(rows, many=True, context=context).data
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)

    def create(self, request, *args, **kwargs):
        write = self.write_serializer_class(data=request.data)
        write.is_valid(raise_exception=True)
        obj, created = self.model.objects.get_or_create(
            user=request.user,
            content_type=write.validated_data["content_type"],
            object_id=write.validated_data["object_id"],
        )
        context = {**self.get_serializer_context(), "items": _items_for([obj])}
        data = self.read_serializer_class(obj, context=context).data
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class LibraryDestroyView(generics.DestroyAPIView):
    """DELETE one of the user's own rows; another user's row is simply not found."""

    permission_classes = [IsVerifiedUser]
    throttle_scope = "library"
    model = None

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class FavoriteListCreateView(LibraryListCreateView):
    model = Favorite


class FavoriteDestroyView(LibraryDestroyView):
    model = Favorite


class WatchlistListCreateView(LibraryListCreateView):
    model = WatchlistItem
    write_serializer_class = WatchlistWriteSerializer


class WatchlistDestroyView(LibraryDestroyView):
    model = WatchlistItem


class BookmarkListCreateView(LibraryListCreateView):
    model = Bookmark


class BookmarkDestroyView(LibraryDestroyView):
    model = Bookmark


class FollowingListCreateView(LibraryListCreateView):
    model = Following
    read_serializer_class = FollowingSerializer


class FollowingDetailView(generics.UpdateAPIView, generics.DestroyAPIView):
    """PATCH ``notifications_enabled`` or DELETE one of the user's follows.

    No GET, and the update serializer accepts nothing but ``notifications_enabled``,
    so the content an item points at can never be reassigned through here.
    """

    permission_classes = [IsVerifiedUser]
    throttle_scope = "library"
    http_method_names = ["patch", "delete"]
    serializer_class = FollowingUpdateSerializer

    def get_queryset(self):
        return Following.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance.notifications_enabled = serializer.validated_data["notifications_enabled"]
        instance.save(update_fields=["notifications_enabled", "updated_at"])
        context = {**self.get_serializer_context(), "items": _items_for([instance])}
        return Response(FollowingSerializer(instance, context=context).data)


class LibraryStatusView(APIView):
    """One call returning the user's button states for a single item.

    ``GET library/status/?content_type=&object_id=`` -> the four booleans plus the
    follow's ``notifications_enabled`` (null when not followed), so the UI can
    render every toggle for an item without four separate requests.
    """

    permission_classes = [IsVerifiedUser]
    throttle_scope = "library"

    def get(self, request):
        content_type = request.query_params.get("content_type")
        object_id = request.query_params.get("object_id")
        if content_type not in LIBRARY_CONTENT_TYPES or not (object_id or "").isdigit():
            return Response(
                {"detail": "content_type and a numeric object_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        object_id = int(object_id)
        key = {"user": request.user, "content_type": content_type, "object_id": object_id}
        following = Following.objects.filter(**key).first()
        return Response(
            {
                "favorite": Favorite.objects.filter(**key).exists(),
                "watchlist": WatchlistItem.objects.filter(**key).exists(),
                "bookmark": Bookmark.objects.filter(**key).exists(),
                "following": following is not None,
                "notifications_enabled": following.notifications_enabled if following else None,
            }
        )
