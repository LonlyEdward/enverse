# EnVerse

A personalized entertainment and sports discovery platform that automatically
tracks, organizes and notifies users about upcoming movies, TV, anime, games and
football events.

Backend: Django 6.1 + Django REST Framework, Celery (Redis), PostgreSQL.
Frontend (later phases): React + Vite + TypeScript.

Build plan and progress live in `enverse-handoff/docs/` (`BUILD_PLAN.md`,
`PROGRESS.md`, `SPEC.md`).

## Quick start (Docker)

Everything runs in Docker Compose. You need Docker and the Compose plugin.

```bash
# 1. Clone, then create your local env file from the template.
cp .env.example .env
# Edit .env if you like. For local development the defaults are fine: the
# compose file already supplies SECRET_KEY, DEBUG and REDIS_URL dev defaults.

# 2. Build and start db, redis, backend, the Celery worker and beat.
docker compose up -d --build

# 3. Apply database migrations.
docker compose exec -u "$(id -u):$(id -g)" backend python manage.py migrate

# 4. Check it is alive.
curl http://localhost:8000/api/v1/health/         # -> {"status": "ok"}
curl http://localhost:8000/api/v1/health/ready/   # -> {"status":"ok","checks":{...}}
```

The backend API is served at <http://localhost:8000/> and the Django admin at
<http://localhost:8000/admin/>.

## Common commands

```bash
# Run the test suite (PostgreSQL in Docker).
docker compose exec backend python manage.py test

# Create migrations after a model change (name the apps explicitly).
# The -u flag keeps generated files owned by you, not root.
docker compose exec -u "$(id -u):$(id -g)" backend python manage.py makemigrations <app>

# Create an admin user. It asks for an email AND a username, because the User
# model keeps a required unique username (USERNAME_FIELD is email).
docker compose exec backend python manage.py createsuperuser

# Tail the backend logs.
docker compose logs -f backend
```

`docker compose down` stops the stack but keeps the database. `docker compose
down -v` also deletes the Postgres volume — only use `-v` when you mean it.

## Frontend (web app)

The React app lives in `frontend/` (React 19 + Vite + TypeScript, Tailwind,
React Router, TanStack Query). `docker compose up` already starts it at
<http://localhost:5173/> with hot reload. To run it on its own instead:

```bash
cd frontend
cp .env.example .env     # VITE_API_URL=http://localhost:8000/api/v1
npm install
npm run dev              # http://localhost:5173
```

The app talks to the API over `VITE_API_URL` and generates its TypeScript types
from the backend's OpenAPI schema:

```bash
npm run gen:api          # regenerate src/api/schema.ts from /api/schema/
npm run typecheck        # tsc strict
npm run lint             # oxlint
npm run build            # production build
```

Seed demo content first (see "Demo data" below) so the lists have something to
show. Design tokens and frontend conventions are documented in
`enverse-handoff/docs/DESIGN.md`.

## Configuration

All configuration comes from environment variables; see `.env.example` for the
full list with comments. `DEBUG` defaults to **False** and production refuses to
start without a `SECRET_KEY`.

## API documentation

The API is self-describing through an OpenAPI 3 schema (drf-spectacular):

- **Schema (YAML):** <http://localhost:8000/api/schema/>
- **Swagger UI:** <http://localhost:8000/api/docs/>
- **ReDoc:** <http://localhost:8000/api/redoc/>

This schema is the contract the frontend generates its TypeScript types from. A
hand-maintained endpoint summary also lives in `enverse-handoff/docs/API.md`.

## Demo data (no API keys needed)

External content syncs need API keys, but you can fill the database with realistic
fake content to develop the UI:

```bash
docker compose exec -u "$(id -u):$(id -g)" backend python manage.py seed_demo --count 200
```

It is deterministic and idempotent (re-running refreshes the same `demo-*` rows),
makes no external calls, and assigns trending ranks so every list, trending,
calendar and dashboard view has something to show.

## Throttling

Rate limits use DRF's `ScopedRateThrottle` backed by the Redis cache, so the
counters are **global** across all Gunicorn workers (the 6th `auth/register/` call
within an hour gets a 429 no matter which worker serves it). Note the trade-off:
if Redis is unavailable, throttled endpoints fail closed (HTTP 500) rather than
letting unlimited traffic through.
