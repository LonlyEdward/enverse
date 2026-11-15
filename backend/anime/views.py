"""Public read endpoints for anime."""

from django.db.models import F
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny

from .filters import AnimeFilterSet
from .models import Anime, AnimeEpisode
from .serializers import AnimeDetailSerializer, AnimeEpisodeSerializer, AnimeListSerializer


class AnimeListView(generics.ListAPIView):
    queryset = Anime.objects.all()
    serializer_class = AnimeListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AnimeFilterSet
    ordering_fields = ["rating", "popularity", "title", "next_airing_at"]


class AnimeTrendingView(generics.ListAPIView):
    serializer_class = AnimeListSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Anime.objects.filter(trending_rank__isnull=False).order_by("trending_rank")


class AnimeAiringView(generics.ListAPIView):
    """Currently releasing anime, soonest next episode first."""

    serializer_class = AnimeListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Anime.objects.filter(airing_status=Anime.AiringStatus.RELEASING).order_by(
            F("next_airing_at").asc(nulls_last=True)
        )


class AnimeDetailView(generics.RetrieveAPIView):
    queryset = Anime.objects.prefetch_related("episodes")
    serializer_class = AnimeDetailSerializer
    permission_classes = [AllowAny]


class AnimeEpisodesView(generics.ListAPIView):
    serializer_class = AnimeEpisodeSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return AnimeEpisode.objects.none()
        anime = get_object_or_404(Anime, pk=self.kwargs["pk"])
        return anime.episodes.all()
