/**
 * Token storage.
 *
 * Access token: kept in memory only. It is short-lived (15 min) and never
 * touches disk, so an XSS payload cannot read it from storage after the tab
 * closes, and it is gone on reload (we re-mint it from the refresh token).
 *
 * Refresh token: kept in localStorage so the session survives a reload. This
 * is a deliberate trade-off — localStorage is readable by any script on the
 * origin, so an XSS bug could steal it. We accept it because the backend
 * rotates the refresh token on every use and blacklists the old one, which
 * bounds the damage, and the alternative (an httpOnly cookie) needs CSRF
 * handling the API is not set up for. This is documented in docs/DESIGN.md.
 */
const REFRESH_KEY = 'enverse-refresh'

let accessToken: string | null = null

export function getAccessToken(): string | null {
  return accessToken
}

export function getRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_KEY)
  } catch {
    return null
  }
}

export function setTokens(tokens: {
  access: string
  refresh?: string | null
}): void {
  accessToken = tokens.access
  if (tokens.refresh) {
    try {
      localStorage.setItem(REFRESH_KEY, tokens.refresh)
    } catch {
      // Storage can be unavailable (private mode); the in-memory access token
      // still works for this tab.
    }
  }
}

export function clearTokens(): void {
  accessToken = null
  try {
    localStorage.removeItem(REFRESH_KEY)
  } catch {
    // ignore
  }
}

export function hasRefreshToken(): boolean {
  return getRefreshToken() !== null
}
