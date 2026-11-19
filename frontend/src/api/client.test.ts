import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { API_ORIGIN, onAuthLost, rawGet } from './client'
import { ApiError } from './errors'
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from './tokens'

const REFRESH_URL = `${API_ORIGIN}/api/v1/auth/token/refresh/`
const DATA_PATH = '/api/v1/dashboard/'

/** A JSON Response, as the real fetch would return. */
function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function urlOf(input: RequestInfo | URL): string {
  return input instanceof Request ? input.url : String(input)
}

function authHeaderOf(input: RequestInfo | URL | undefined): string | null {
  return input instanceof Request ? input.headers.get('Authorization') : null
}

const fetchMock = vi.fn<typeof fetch>()

beforeEach(() => {
  clearTokens()
  localStorage.clear()
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('authFetch (via rawGet)', () => {
  it('attaches the access token and passes a success through without refreshing', async () => {
    setTokens({ access: 'acc-1', refresh: 'ref-1' })
    fetchMock.mockResolvedValue(jsonResponse({ ok: true }, 200))

    const result = await rawGet<{ ok: boolean }>(DATA_PATH)

    expect(result).toEqual({ ok: true })
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(authHeaderOf(fetchMock.mock.calls[0]?.[0])).toBe('Bearer acc-1')
  })

  it('refreshes once on a 401, stores the rotated tokens and retries with the new access token', async () => {
    setTokens({ access: 'acc-1', refresh: 'ref-1' })
    let refreshBody: unknown
    fetchMock.mockImplementation(async (input, init) => {
      if (urlOf(input) === REFRESH_URL) {
        refreshBody = JSON.parse(String(init?.body))
        return jsonResponse({ access: 'acc-2', refresh: 'ref-2' }, 200)
      }
      // The stale access token is rejected; the retry carries the new one.
      return authHeaderOf(input) === 'Bearer acc-1'
        ? jsonResponse({ detail: 'Token expired' }, 401)
        : jsonResponse({ ok: true }, 200)
    })

    const result = await rawGet<{ ok: boolean }>(DATA_PATH)

    expect(result).toEqual({ ok: true })
    expect(refreshBody).toEqual({ refresh: 'ref-1' })
    expect(getAccessToken()).toBe('acc-2')
    expect(getRefreshToken()).toBe('ref-2')
    // original 401 + refresh + retry
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(authHeaderOf(fetchMock.mock.calls[2]?.[0])).toBe('Bearer acc-2')
  })

  it('refreshes only once when several requests 401 at the same time', async () => {
    setTokens({ access: 'acc-1', refresh: 'ref-1' })
    let refreshCalls = 0
    fetchMock.mockImplementation(async (input) => {
      if (urlOf(input) === REFRESH_URL) {
        refreshCalls += 1
        return jsonResponse({ access: 'acc-2', refresh: 'ref-2' }, 200)
      }
      return authHeaderOf(input) === 'Bearer acc-1'
        ? jsonResponse({ detail: 'Token expired' }, 401)
        : jsonResponse({ ok: true }, 200)
    })

    const results = await Promise.all([
      rawGet<{ ok: boolean }>('/api/v1/dashboard/'),
      rawGet<{ ok: boolean }>('/api/v1/notifications/'),
      rawGet<{ ok: boolean }>('/api/v1/library/'),
    ])

    expect(results).toEqual([{ ok: true }, { ok: true }, { ok: true }])
    expect(refreshCalls).toBe(1)
  })

  it('notifies auth-lost listeners and clears tokens when the refresh itself fails', async () => {
    setTokens({ access: 'acc-1', refresh: 'ref-1' })
    const onLost = vi.fn()
    const unsubscribe = onAuthLost(onLost)
    fetchMock.mockImplementation(async (input) => {
      if (urlOf(input) === REFRESH_URL) {
        return jsonResponse({ detail: 'Invalid refresh token' }, 401)
      }
      return jsonResponse({ detail: 'Token expired' }, 401)
    })

    await expect(rawGet(DATA_PATH)).rejects.toBeInstanceOf(ApiError)

    expect(onLost).toHaveBeenCalledTimes(1)
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
    unsubscribe()
  })

  it('does not attempt a refresh on a 401 when there is no refresh token', async () => {
    setTokens({ access: 'acc-1' }) // no refresh token stored
    const onLost = vi.fn()
    const unsubscribe = onAuthLost(onLost)
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Token expired' }, 401))

    await expect(rawGet(DATA_PATH)).rejects.toMatchObject({ status: 401 })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(onLost).not.toHaveBeenCalled()
    unsubscribe()
  })
})
