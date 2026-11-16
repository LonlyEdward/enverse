import { api } from './client'
import { unwrap } from './errors'
import { clearTokens, getRefreshToken, setTokens } from './tokens'
import type { LoginResponse, User } from './types'

/** Log in, store the returned tokens, and return the user. */
export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const result = unwrap(
    await api.POST('/api/v1/auth/login/', { body: { email, password } }),
  ) as unknown as LoginResponse
  setTokens({ access: result.access, refresh: result.refresh })
  return result
}

/** Register a new account. Does not log in (the user must verify first). */
export async function register(input: {
  email: string
  password: string
  display_name?: string
}): Promise<void> {
  unwrap(await api.POST('/api/v1/auth/register/', { body: input }))
}

/** Confirm an email address from the token in the verification link. */
export async function verifyEmail(token: string): Promise<void> {
  unwrap(await api.POST('/api/v1/auth/verify-email/', { body: { token } }))
}

/** Ask for a fresh verification email (requires being logged in). */
export async function resendVerification(): Promise<void> {
  unwrap(await api.POST('/api/v1/auth/resend-verification/'))
}

/** Start a password reset. Always succeeds server-side (no account
 *  enumeration), so the UI shows the same message either way. */
export async function requestPasswordReset(email: string): Promise<void> {
  unwrap(await api.POST('/api/v1/auth/password-reset/', { body: { email } }))
}

/** Finish a password reset from the link's uid+token. Does not log in. */
export async function confirmPasswordReset(input: {
  uid: string
  token: string
  new_password: string
}): Promise<void> {
  unwrap(
    await api.POST('/api/v1/auth/password-reset/confirm/', { body: input }),
  )
}

/** Fetch the current user from a valid access token. */
export async function fetchMe(): Promise<User> {
  return unwrap(await api.GET('/api/v1/users/me/'))
}

/** Update the editable profile fields (display name, avatar URL). Email is
 *  read-only server-side. Returns the refreshed user. */
export async function updateProfile(patch: {
  display_name?: string
  avatar_url?: string
}): Promise<User> {
  return unwrap(await api.PATCH('/api/v1/users/me/', { body: patch }))
}

/** Blacklist the refresh token server-side, then drop local tokens. This is
 *  best-effort: tokens are cleared even if the network call fails. */
export async function logout(): Promise<void> {
  const refresh = getRefreshToken()
  try {
    if (refresh) {
      await api.POST('/api/v1/auth/logout/', { body: { refresh } })
    }
  } finally {
    clearTokens()
  }
}
