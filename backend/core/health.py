"""Health-check endpoints.

Deliberately plain Django views, not DRF: authentication, throttling or a
pagination misconfiguration must never be able to break a health check. A load
balancer needs these to answer even when the rest of the API is unhappy.
"""

import logging

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)

READINESS_CACHE_KEY = "health:ready"


# csrf_exempt so an unsafe method returns a clean 405 from require_GET rather
# than a 403 from the CSRF middleware; health checks must not depend on CSRF.
@csrf_exempt
@require_GET
@never_cache
def live(request):
    """Liveness: the process is up and serving. Touches no external resource."""
    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_GET
@never_cache
def ready(request):
    """Readiness: the database and cache are actually reachable.

    Returns 503 if either dependency fails. Exception details are logged
    server-side only; the response body never leaks internals.
    """
    checks = {"database": "ok", "cache": "ok"}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Readiness check: database is unavailable")
        checks["database"] = "error"

    try:
        cache.set(READINESS_CACHE_KEY, "1", 10)
        if cache.get(READINESS_CACHE_KEY) != "1":
            raise RuntimeError("cache round-trip returned an unexpected value")
    except Exception:
        logger.exception("Readiness check: cache is unavailable")
        checks["cache"] = "error"

    healthy = all(value == "ok" for value in checks.values())
    status_code = 200 if healthy else 503
    return JsonResponse({"status": "ok" if healthy else "error", "checks": checks}, status=status_code)
