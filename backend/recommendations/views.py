"""Read the user's recommendations (computed lazily the first time) and refresh them."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.registry import load_content

from .models import Recommendation
from .serializers import RecommendationSerializer
from .services import recompute_for_user


class RecommendationListView(generics.ListAPIView):
    """``GET recommendations/?type=`` — computed on first access, then just read."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "recommendations"
    serializer_class = RecommendationSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Recommendation.objects.none()
        qs = Recommendation.objects.filter(user=self.request.user)
        content_type = self.request.query_params.get("type")
        if content_type:
            qs = qs.filter(content_type=content_type)
        return qs

    def list(self, request, *args, **kwargs):
        # Lazy first compute: a brand-new user has none until something generates them.
        if not Recommendation.objects.filter(user=request.user).exists():
            recompute_for_user(request.user)
        rows = list(self.filter_queryset(self.get_queryset()))
        items = load_content([(row.content_type, row.object_id) for row in rows])
        data = self.get_serializer(rows, many=True, context={**self.get_serializer_context(), "items": items}).data
        return Response(data)


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
class RecommendationRefreshView(APIView):
    """``POST recommendations/refresh/`` — recompute now (tightly throttled)."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "recommendations_refresh"

    def post(self, request):
        count = recompute_for_user(request.user)
        return Response({"recomputed": count}, status=status.HTTP_200_OK)
