FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY . .

# Collect static files at build time. SECRET_KEY is a throwaway value just so
# settings import succeeds; no database is touched by collectstatic.
RUN SECRET_KEY=build-only python manage.py collectstatic --noinput

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Gunicorn in production. Compose overrides this with runserver for development.
# sh -c so the ${PORT}/${WEB_CONCURRENCY} environment variables expand.
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --timeout 60 --access-logfile -"]
