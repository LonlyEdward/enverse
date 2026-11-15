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

/** Fetch the current user from a valid access token. */
export async function fetchMe(): Promise<User> {
  return unwrap(await api.GET('/api/v1/users/me/'))
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
