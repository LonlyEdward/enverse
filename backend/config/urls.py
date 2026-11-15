"""Root URL configuration.

All API routes live under ``/api/v1/``. Each app contributes its own include as
its phase lands; for now only the health checks exist.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from core import health

# Everything under /api/v1/. Health is wired directly because it is a pair of
# plain views; feature apps are added here with include() as they are built.
api_v1_patterns = [
    path("health/", health.live, name="health-live"),
    path("health/ready/", health.ready, name="health-ready"),
    path("", include("accounts.urls")),
    path("", include("movies.urls")),
    path("", include("tv.urls")),
    path("", include("anime.urls")),
    path("", include("games.urls")),
    path("", include("sports.urls")),
    path("", include("library.urls")),
    path("", include("content.urls")),
    path("", include("notifications.urls")),
    path("", include("recommendations.urls")),
    path("", include("agenda.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1_patterns, "api"), namespace="v1")),
    # OpenAPI schema and human-browsable docs (the frontend contract).
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
