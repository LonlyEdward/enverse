import { beforeEach, describe, expect, it } from 'vitest'

import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  hasRefreshToken,
  setTokens,
} from './tokens'

beforeEach(() => {
  clearTokens()
  localStorage.clear()
})

describe('token storage', () => {
  it('keeps the access token in memory and the refresh token in localStorage', () => {
    setTokens({ access: 'access-1', refresh: 'refresh-1' })
    expect(getAccessToken()).toBe('access-1')
    expect(getRefreshToken()).toBe('refresh-1')
    expect(localStorage.getItem('enverse-refresh')).toBe('refresh-1')
    expect(hasRefreshToken()).toBe(true)
  })

  it('clears both tokens', () => {
    setTokens({ access: 'access-1', refresh: 'refresh-1' })
    clearTokens()
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
    expect(hasRefreshToken()).toBe(false)
  })

  it('keeps the existing refresh token when a rotation omits it', () => {
    setTokens({ access: 'access-1', refresh: 'refresh-1' })
    setTokens({ access: 'access-2' })
    expect(getAccessToken()).toBe('access-2')
    expect(getRefreshToken()).toBe('refresh-1')
  })

  it('reports no refresh token before anything is stored', () => {
    expect(hasRefreshToken()).toBe(false)
    expect(getAccessToken()).toBeNull()
  })
})
