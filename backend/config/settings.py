"""Django settings for EnVerse.

Environment-driven and production-minded. Every secret and every toggle comes
from an environment variable; nothing sensitive is hard-coded. See
``config/env.py`` for the parsing helpers and ``.env.example`` for the full list
of variables the app reads.
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

import dj_database_url
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

from config.env import env_bool, env_int, env_list, with_redis_db

BASE_DIR = Path(__file__).resolve().parent.parent

# True while running the test suite. We relax a couple of production-only guards
# (the HTTPS redirect) so tests do not have to speak HTTPS; individual tests
# re-enable them with override_settings when they need to assert that behaviour.
TESTING = "test" in sys.argv


# --- Core -------------------------------------------------------------------

DEBUG = env_bool("DEBUG", False)  # Default False: production must opt in to debug.

# SECRET_KEY must come from the environment in production. In DEBUG we fall back
# to a throwaway key so a fresh clone runs without ceremony; in production a
# missing key is a hard error rather than a silent insecure default.
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-dev-only-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured("SECRET_KEY environment variable is required when DEBUG is off.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")  # entries need a scheme, e.g. https://app.example.com

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Applications -----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # required for ArrayField on Django 6+ (system check postgres.E005)
    # Third party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    # Local
    "accounts",
    "content",
    "core",
    "movies",
    "tv",
    "anime",
    "games",
    "sports",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # must sit right after SecurityMiddleware
    "corsheaders.middleware.CorsMiddleware",  # must come before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Database ---------------------------------------------------------------
# Prefer a single DATABASE_URL (how Railway and most hosts hand out Postgres);
# fall back to the discrete POSTGRES_* variables used by docker-compose locally.
# .get(..., "") keeps settings importable during the Docker build's collectstatic
# step, which runs with no database variables set.

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, conn_health_checks=True),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", ""),
            "USER": os.environ.get("POSTGRES_USER", ""),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ.get("POSTGRES_HOST", "db"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 600,
            "CONN_HEALTH_CHECKS": True,
        }
    }


# --- Cache & Redis ----------------------------------------------------------
# Celery uses Redis database 0; the Django cache uses database 1 on purpose:
# cache.clear() issues FLUSHDB, which on database 0 would wipe the Celery queue.

REDIS_URL = os.environ.get("REDIS_URL", "")
if TESTING:
    # Tests must not depend on (or clobber) a shared Redis; an in-process cache
    # keeps throttle counters and cached values isolated per test run.
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
elif REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": with_redis_db(REDIS_URL, 1),
            "KEY_PREFIX": "enverse",
        }
    }
else:
    # No Redis configured (tests, bare local runs): an in-process cache is enough.
    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }


# --- Password validation ----------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Internationalization ---------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# --- Static files -----------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}


# --- Security (production only) ---------------------------------------------
# Skipped in DEBUG and during tests so local work and the test client do not
# have to speak HTTPS. Tests that assert the redirect behaviour turn it back on
# with override_settings.

if not DEBUG and not TESTING:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    # Platform health checks hit plain HTTP, so never redirect them.
    SECURE_REDIRECT_EXEMPT = [r"^api/v1/health/"]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Start the HSTS window small and raise it to a year once HTTPS is proven.
    # check --deploy still warns about HSTS_INCLUDE_SUBDOMAINS/PRELOAD; both are
    # hard-to-undo commitments about the whole domain, so we leave them off on
    # purpose (documented in docs/PROGRESS.md).
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 3600)


# --- CORS -------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS") or [FRONTEND_URL]


# --- Email ------------------------------------------------------------------
# Django 6.1 uses MAILERS (EMAIL_* is deprecated). Console backend in dev;
# SMTP in production, selected by an env flag.

if env_bool("EMAIL_USE_SMTP", False):
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": os.environ.get("SMTP_HOST", ""),
                "port": env_int("SMTP_PORT", 587),
                "use_tls": env_bool("SMTP_USE_TLS", True),
                "username": os.environ.get("SMTP_USER", ""),
                "password": os.environ.get("SMTP_PASSWORD", ""),
                "timeout": 10,
            },
        }
    }
else:
    MAILERS = {"default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"}}

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "EnVerse <no-reply@enverse.local>")


# --- External content APIs ---
# Used by the sync tasks (added per phase). When a key is missing, the matching
# sync logs a warning and exits cleanly; tests never call the live APIs.
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
RAWG_API_KEY = os.environ.get("RAWG_API_KEY", "")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "")


# --- Django REST Framework --------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.DefaultPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "register": "5/hour",
        "login": "10/minute",
        "password_reset": "5/hour",
        "resend_verification": "5/hour",
        "library": "120/minute",
        "notifications": "240/minute",
        "search": "60/minute",
        "recommendations": "120/minute",
        "recommendations_refresh": "10/hour",
        "calendar": "60/minute",
    },
    # Throttling trusts X-Forwarded-For; this must equal the number of proxies in
    # front of the app or clients can spoof their IP (too low) or share one bucket
    # (too high). 0 in dev (no proxy), 1 in production (one load balancer).
    "NUM_PROXIES": env_int("NUM_PROXIES", 0 if DEBUG else 1),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}


# --- Celery -----------------------------------------------------------------

CELERY_BROKER_URL = REDIS_URL or "redis://redis:6379/0"
CELERY_TIMEZONE = "UTC"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Static schedule with Celery's built-in scheduler (django-celery-beat does not
# support Django 6.1). Entries are added in the phase that creates the task they
# reference (see docs/BUILD_PLAN.md section 20 for the full target schedule), so
# the schedule only ever names tasks that actually exist and beat never dispatches
# to an unregistered task.
CELERY_BEAT_SCHEDULE = {
    "sync-movies": {"task": "movies.tasks.sync_movies", "schedule": crontab(minute=0, hour="*/6")},
    "sync-tv": {"task": "tv.tasks.sync_tv", "schedule": crontab(minute=15, hour="*/6")},
    "sync-anime": {"task": "anime.tasks.sync_anime", "schedule": crontab(minute=30, hour="*/2")},
    "sync-games": {"task": "games.tasks.sync_games", "schedule": crontab(minute=45, hour="3,15")},
    "sync-football": {"task": "sports.tasks.sync_football", "schedule": crontab(minute=5, hour="*/3")},
}


# --- Logging ----------------------------------------------------------------
# One console handler on the root logger writing to stdout. The django logger
# carries no handlers of its own and propagates, so records are not printed twice.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {"handlers": [], "level": "INFO", "propagate": True},
    },
}
