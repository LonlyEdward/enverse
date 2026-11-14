"""Public read endpoints for games."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny

from .filters import GameFilterSet
from .models import Game
from .serializers import GameDetailSerializer, GameListSerializer


class GameListView(generics.ListAPIView):
    queryset = Game.objects.all()
    serializer_class = GameListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = GameFilterSet
    ordering_fields = ["release_date", "rating", "metacritic", "popularity", "title"]


class GameTrendingView(generics.ListAPIView):
    serializer_class = GameListSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Game.objects.filter(trending_rank__isnull=False).order_by("trending_rank")


class GameDetailView(generics.RetrieveAPIView):
    queryset = Game.objects.all()
    serializer_class = GameDetailSerializer
    permission_classes = [AllowAny]
