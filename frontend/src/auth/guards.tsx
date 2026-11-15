import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { EmptyState } from '@/components/EmptyState'
import { Spinner } from '@/components/Spinner'
import { useAuth } from './AuthContext'

function FullPageSpinner() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <Spinner label="Loading your session" />
    </div>
  )
}

/** Gate a route behind being logged in. Sends anonymous users to login and
 *  remembers where they were headed. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <FullPageSpinner />
  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ next: location.pathname }} />
  }
  return <>{children}</>
}

/** Gate a route behind a verified email (library, following, etc.). */
export function RequireVerified({ children }: { children: ReactNode }) {
  const { status, isVerified } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <FullPageSpinner />
  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ next: location.pathname }} />
  }
  if (!isVerified) {
    return (
      <EmptyState
        title="Verify your email first"
        description="This feature needs a verified email. Check your inbox for the link, or resend it from Settings."
      />
    )
  }
  return <>{children}</>
}
