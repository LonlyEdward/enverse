"""Public read endpoints for TV shows."""

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny

from .filters import TVFilterSet
from .models import TVShow
from .serializers import TVSeasonSerializer, TVShowDetailSerializer, TVShowListSerializer


class TVListView(generics.ListAPIView):
    queryset = TVShow.objects.all()
    serializer_class = TVShowListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TVFilterSet
    ordering_fields = ["first_air_date", "rating", "popularity", "title"]


class TVTrendingView(generics.ListAPIView):
    serializer_class = TVShowListSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return TVShow.objects.filter(trending_rank__isnull=False).order_by("trending_rank")


class TVDetailView(generics.RetrieveAPIView):
    # Prefetch seasons so the detail serializer does not issue an extra query.
    queryset = TVShow.objects.prefetch_related("seasons")
    serializer_class = TVShowDetailSerializer
    permission_classes = [AllowAny]


class TVSeasonsView(generics.ListAPIView):
    serializer_class = TVSeasonSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        # 404 when the show itself does not exist (not just an empty list).
        show = get_object_or_404(TVShow, pk=self.kwargs["pk"])
        return show.seasons.all()
