import { execFileSync } from 'node:child_process'
import path from 'node:path'

import { expect, test } from '@playwright/test'

// The repo root, where docker-compose.yaml lives, resolved from this file
// (tests live in e2e/tests, so two levels up).
const REPO_ROOT = path.resolve(__dirname, '..', '..')

/**
 * Fetch a user's email-verification token straight from the backend, using the
 * same function the app uses to build the emailed link.
 *
 * Why not read the console email from the logs: the dev console backend
 * quoted-printable-encodes and soft-wraps the link, so the token is split and
 * escaped across log lines and is brittle to parse. Email *delivery* is covered
 * by the backend test suite; here we exercise the UI verify → login → use flow,
 * and take the token the robust way.
 */
function fetchVerificationToken(email: string): string {
  const script = [
    'from django.contrib.auth import get_user_model',
    'from accounts.tokens import make_email_verification_token',
    'U = get_user_model()',
    `print("TOKEN:" + make_email_verification_token(U.objects.get(email="${email}")))`,
  ].join('; ')

  const out = execFileSync(
    'docker',
    ['compose', 'exec', '-T', 'backend', 'python', 'manage.py', 'shell', '-c', script],
    { cwd: REPO_ROOT, encoding: 'utf8' },
  )
  const match = out.match(/TOKEN:(\S+)/)
  if (!match) throw new Error(`No token in backend output:\n${out}`)
  return match[1]!
}

test('register, verify, onboard, favourite a movie, see it in the library, open the calendar', async ({
  page,
}) => {
  const email = `e2e+${Date.now()}@example.com`
  const password = 'E2ePassw0rd!'

  // --- Register -----------------------------------------------------------
  await page.goto('/register')
  await page.getByLabel('Display name').fill('E2E Tester')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page.getByText('Check your inbox')).toBeVisible()

  // --- Verify (token fetched from the backend, then the real verify page) --
  const token = fetchVerificationToken(email)
  await page.goto(`/verify-email?token=${encodeURIComponent(token)}`)
  await expect(page.getByText(/verified/i)).toBeVisible()

  // --- Log in -------------------------------------------------------------
  await page.goto('/login')
  const form = page.getByRole('main')
  await form.getByLabel('Email').fill(email)
  await form.getByLabel('Password').fill(password)
  await form.getByRole('button', { name: 'Log in' }).click()

  // A brand-new user is routed into onboarding; skip it.
  await page.waitForURL(/\/(onboarding)?$/)
  const skip = page.getByRole('button', { name: /skip for now/i })
  if (await skip.isVisible().catch(() => false)) {
    await skip.click()
  }

  // --- Favourite a movie --------------------------------------------------
  await page.goto('/movies')
  const firstPoster = page.locator('main a[href^="/movies/"]').first()
  await expect(firstPoster).toBeVisible()
  await firstPoster.click()
  await page.waitForURL(/\/movies\/\d+$/)

  const title = (await page.getByRole('heading', { level: 1 }).first().innerText()).trim()
  const favourite = page.getByRole('button', { name: /^favourite$/i })
  await expect(favourite).toBeVisible()
  await favourite.click()
  await expect(page.getByRole('button', { name: /favourited/i })).toBeVisible()

  // --- See it in the library ---------------------------------------------
  await page.goto('/library')
  await expect(
    page.getByRole('heading', { level: 1, name: /your library/i }),
  ).toBeVisible()
  await expect(page.getByText(title, { exact: true }).first()).toBeVisible()

  // --- Open the calendar --------------------------------------------------
  await page.goto('/calendar')
  await expect(
    page.getByRole('heading', { level: 1, name: /calendar/i }),
  ).toBeVisible()
})
