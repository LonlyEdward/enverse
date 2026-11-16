# EnVerse end-to-end smoke test

A single Playwright test that drives the real app through its most important
path: register → verify email → log in → skip onboarding → favourite a movie →
see it in the library → open the calendar.

It runs against the **already-running Dockerised stack**, not its own server, so
bring the stack up first and make sure content is seeded.

## Run it

```bash
# 1. From the repo root, start the stack and seed demo content.
docker compose up -d
docker compose exec backend python manage.py seed_demo

# 2. Install and run the test (needs Node on the host — Playwright's browsers
#    do not run in the Alpine frontend container).
cd e2e
npm ci
npx playwright install chromium   # first time only; downloads the browser
npx playwright test
```

Override the frontend URL with `E2E_BASE_URL` if you serve it somewhere other
than `http://localhost:5173`.

## Notes

- **Playwright is pinned to 1.62** so it matches the Chromium build already
  cached on the dev machine; bump it together with `npx playwright install`.
- The test fetches the email-verification token directly from the backend
  (`docker compose exec backend …`) rather than scraping it from the console
  email, because the dev console mail backend quoted-printable-encodes and
  soft-wraps the link. Email delivery itself is covered by the backend tests;
  this exercises the UI verify → login → use flow.
- It needs `docker` and `docker compose` on the PATH and must run from a checkout
  whose repo root holds `docker-compose.yaml`.
