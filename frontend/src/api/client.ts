import createClient from 'openapi-fetch'

import { toApiError } from './errors'
import type { paths } from './schema'
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from './tokens'

/**
 * The generated schema keeps the full `/api/v1/...` prefix on every path, so
 * the client's base URL is the API origin (VITE_API_URL with the `/api/v1`
 * suffix stripped). Typed calls then read naturally: api.GET('/api/v1/...').
 */
export const API_ORIGIN = import.meta.env.VITE_API_URL.replace(
  /\/api\/v1\/?$/,
  '',
)

const REFRESH_PATH = '/api/v1/auth/token/refresh/'

// --- Forced-logout notification -------------------------------------------
// When a refresh fails the session is over; AuthProvider subscribes here so it
// can clear the user and send them to the login page.
type AuthLostListener = () => void
const authLostListeners = new Set<AuthLostListener>()

export function onAuthLost(listener: AuthLostListener): () => void {
  authLostListeners.add(listener)
  return () => authLostListeners.delete(listener)
}

function notifyAuthLost(): void {
  clearTokens()
  for (const listener of authLostListeners) listener()
}

// --- Single-flight refresh -------------------------------------------------
// Many requests can 401 at once (e.g. a dashboard firing several queries).
// They must not each refresh; they all await one in-flight refresh instead.
let refreshing: Promise<boolean> | null = null

function ensureRefreshed(): Promise<boolean> {
  if (!refreshing) {
    refreshing = doRefresh().finally(() => {
      refreshing = null
    })
  }
  return refreshing
}

async function doRefresh(): Promise<boolean> {
  const refresh = getRefreshToken()
  if (!refresh) {
    notifyAuthLost()
    return false
  }
  try {
    const res = await fetch(`${API_ORIGIN}${REFRESH_PATH}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    if (!res.ok) {
      notifyAuthLost()
      return false
    }
    const data = (await res.json()) as { access: string; refresh?: string }
    // Rotation is on, so the response carries a fresh refresh token too.
    setTokens({ access: data.access, refresh: data.refresh ?? refresh })
    return true
  } catch {
    notifyAuthLost()
    return false
  }
}

function withAuth(request: Request, token: string | null): Request {
  if (!token) return request
  const headers = new Headers(request.headers)
  headers.set('Authorization', `Bearer ${token}`)
  return new Request(request, { headers })
}

/**
 * fetch wrapper: attach the access token, and on a 401 refresh once (shared
 * across concurrent callers) and retry the original request exactly once.
 */
async function authFetch(request: Request): Promise<Response> {
  // Clone up front: the original stream is consumed by the first send, so the
  // retry needs an untouched copy of the body.
  const retryable = request.clone()

  const res = await fetch(withAuth(request, getAccessToken()))

  const isRefreshCall = request.url.endsWith(REFRESH_PATH)
  if (res.status !== 401 || isRefreshCall || !getRefreshToken()) {
    return res
  }

  const refreshed = await ensureRefreshed()
  if (!refreshed) return res

  return fetch(withAuth(retryable, getAccessToken()))
}

/** The typed API client. Every call is checked against the OpenAPI schema. */
export const api = createClient<paths>({
  baseUrl: API_ORIGIN,
  fetch: authFetch,
})

/**
 * Raw GET for the few endpoints whose query params the schema does not document
 * (the view reads them by hand), so the typed client cannot express them —
 * `meta/genres/?type=` and `search/?q=&type=`. Still goes through authFetch, so
 * auth and refresh apply when relevant. `path` must already be a full
 * `/api/v1/...?query` string with its values encoded.
 */
export async function rawGet<T>(path: string): Promise<T> {
  const res = await authFetch(new Request(`${API_ORIGIN}${path}`))
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw toApiError(body, res.status)
  }
  return (await res.json()) as T
}
