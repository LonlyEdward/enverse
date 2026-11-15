import { MailCheck } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { register } from '@/api/auth'
import { ApiError } from '@/api/errors'
import { AuthCard, FormError } from '@/components/AuthCard'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'

export function RegisterPage() {
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<ApiError | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (password.length < 8) {
      setError(
        new ApiError('', 400, undefined, {
          password: ['Use at least 8 characters.'],
        }),
      )
      return
    }

    setSubmitting(true)
    try {
      await register({
        email,
        password,
        display_name: displayName || undefined,
      })
      setDone(true)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err
          : new ApiError('Could not create your account. Try again.', 0),
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (done) {
    return (
      <AuthCard
        title="Check your inbox"
        subtitle={`We sent a verification link to ${email}.`}
      >
        <div className="flex flex-col items-center gap-4 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-success/15 text-success">
            <MailCheck size={26} aria-hidden="true" />
          </span>
          <p className="text-sm text-fg-muted">
            Open the link to verify your email, then log in. The link expires in
            a few days — you can request another from the login screen.
          </p>
          <Link to="/login">
            <Button variant="outline">Go to login</Button>
          </Link>
        </div>
      </AuthCard>
    )
  }

  const topError =
    error && Object.keys(error.fieldErrors).length === 0 && error.message
      ? error.message
      : null

  return (
    <AuthCard
      title="Create your account"
      subtitle="Track releases across movies, TV, anime, games and football."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-brand hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        {topError && <FormError message={topError} />}
        <Input
          label="Display name"
          hint="Optional — how we greet you."
          name="display_name"
          autoComplete="nickname"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          error={error?.fieldErrors.display_name?.[0]}
        />
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
        <Input
          label="Password"
          type="password"
          name="password"
          autoComplete="new-password"
          required
          hint="At least 8 characters."
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={error?.fieldErrors.password?.[0]}
        />
        <Button type="submit" size="lg" loading={submitting} className="mt-1">
          Create account
        </Button>
      </form>
    </AuthCard>
  )
}
