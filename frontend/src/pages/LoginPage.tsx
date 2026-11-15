import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError } from '@/api/errors'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { Logo } from '@/components/Logo'
import { useToast } from '@/components/toast'

interface LocationState {
  next?: string
}

/** Minimal login form. The full auth suite (register, verification, password
 *  reset, onboarding) is built in Phase 14; this proves the token plumbing. */
export function LoginPage() {
  const { login } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const next = (location.state as LocationState | null)?.next ?? '/'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
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
      navigate(next, { replace: true })
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Could not log in. Please try again.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-sm flex-col justify-center">
      <div className="mb-8 flex flex-col items-center gap-3 text-center">
        <Logo />
        <h1 className="text-2xl font-semibold text-fg">Welcome back</h1>
        <p className="text-sm text-fg-muted">
          Log in to pick up where you left off.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        {error && (
          <p
            role="alert"
            className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
          >
            {error}
          </p>
        )}
        <Input
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label="Password"
          type="password"
          name="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Button type="submit" size="lg" loading={submitting} className="mt-1">
          Log in
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-fg-muted">
        New here?{' '}
        <Link to="/" className="font-medium text-brand hover:underline">
          Account sign-up arrives in the next phase.
        </Link>
      </p>
    </div>
  )
}
