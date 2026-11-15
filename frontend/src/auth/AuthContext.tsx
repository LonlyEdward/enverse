import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import type { ReactNode } from 'react'

import {
  fetchMe,
  login as loginRequest,
  logout as logoutRequest,
} from '@/api/auth'
import { onAuthLost } from '@/api/client'
import { hasRefreshToken } from '@/api/tokens'
import type { User } from '@/api/types'

type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

interface AuthContextValue {
  user: User | null
  status: AuthStatus
  isVerified: boolean
  login: (email: string, password: string) => Promise<User>
  logout: () => Promise<void>
  /** Replace the cached user, e.g. after editing the profile. */
  setUser: (user: User | null) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  // Restore the session on load: if a refresh token survived, the API client
  // will mint an access token on the first 401 from /users/me/.
  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      if (!hasRefreshToken()) {
        if (!cancelled) setStatus('anonymous')
        return
      }
      try {
        const me = await fetchMe()
        if (!cancelled) {
          setUser(me)
          setStatus('authenticated')
        }
      } catch {
        if (!cancelled) {
          setUser(null)
          setStatus('anonymous')
        }
      }
    }

    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [])

  // If a refresh fails mid-session, the client tells us the session is over.
  useEffect(
    () =>
      onAuthLost(() => {
        setUser(null)
        setStatus('anonymous')
      }),
    [],
  )

  const login = useCallback(async (email: string, password: string) => {
    const result = await loginRequest(email, password)
    setUser(result.user)
    setStatus('authenticated')
    return result.user
  }, [])

  const logout = useCallback(async () => {
    await logoutRequest()
    setUser(null)
    setStatus('anonymous')
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      isVerified: user?.is_email_verified ?? false,
      login,
      logout,
      setUser,
    }),
    [user, status, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
