import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/errors'
import { getGenrePreferences } from '@/api/preferences'
import { useAuth } from '@/auth/AuthContext'
import { AuthCard, FormError } from '@/components/AuthCard'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { useToast } from '@/components/toast'

interface LocationState {
  next?: string
}

/** Send brand-new users to onboarding, but only when they log into the default
 *  landing (not a specific guarded page) and have no genres saved yet. A local
 *  flag avoids re-prompting someone who already skipped onboarding here. */
async function destinationAfterLogin(next: string): Promise<string> {
  if (next !== '/') return next
  try {
    if (localStorage.getItem('enverse-onboarded')) return next
  } catch {
    // ignore unavailable storage
  }
  try {
    const prefs = await getGenrePreferences()
    return prefs.length === 0 ? '/onboarding' : next
  } catch {
    return next
  }
}

export function LoginPage() {
  const { login } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const next = (location.state as LocationState | null)?.next ?? '/'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<ApiError | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const user = await login(email, password)
      toast({
        title: `Welcome back${user.display_name ? `, ${user.display_name}` : ''}`,
        tone: 'success',
      })
      navigate(await destinationAfterLogin(next), { replace: true })
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err
          : new ApiError('Could not log in. Please try again.', 0),
      )
    } finally {
      setSubmitting(false)
    }
  }

  // A plain 401 ("No active account…") has no field errors, so show it on top.
  const topError =
    error && Object.keys(error.fieldErrors).length === 0 ? error.message : null

  return (
    <AuthCard
      title="Welcome back"
      subtitle="Log in to pick up where you left off."
      footer={
        <>
          New to EnVerse?{' '}
          <Link
            to="/register"
            className="font-medium text-brand hover:underline"
          >
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        {topError && <FormError message={topError} />}
        <Input
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={error?.fieldErrors.email?.[0]}
        />
        <div className="flex flex-col gap-1.5">
          <Input
            label="Password"
            type="password"
            name="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={error?.fieldErrors.password?.[0]}
          />
          <Link
            to="/forgot-password"
            className="self-end text-xs font-medium text-fg-muted hover:text-brand"
          >
            Forgot password?
          </Link>
        </div>
        <Button type="submit" size="lg" loading={submitting} className="mt-1">
          Log in
        </Button>
      </form>
    </AuthCard>
  )
}
