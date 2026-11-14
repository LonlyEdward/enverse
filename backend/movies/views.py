"""Public read endpoints for movies. Browsing does not require an account."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny

from .filters import MovieFilterSet
from .models import Movie
from .serializers import MovieDetailSerializer, MovieListSerializer


class MovieListView(generics.ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = MovieFilterSet
    ordering_fields = ["release_date", "rating", "popularity", "title"]
    # No explicit `ordering` so the model's default ordering applies by default.


class MovieTrendingView(generics.ListAPIView):
    serializer_class = MovieListSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # the trending set is small and fully ranked

    def get_queryset(self):
        return Movie.objects.filter(trending_rank__isnull=False).order_by("trending_rank")


class MovieDetailView(generics.RetrieveAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieDetailSerializer
    permission_classes = [AllowAny]
