import { defineConfig, devices } from '@playwright/test'

/**
 * Smoke test configuration. It drives the already-running Dockerised app
 * (`docker compose up`) rather than starting its own server, because the full
 * stack (db, redis, backend, worker, beat, frontend) must be up and seeded.
 *
 * Override the frontend URL with E2E_BASE_URL if you serve it elsewhere.
 */
export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    headless: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
