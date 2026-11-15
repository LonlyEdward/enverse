import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { confirmPasswordReset } from '@/api/auth'
import { ApiError } from '@/api/errors'
import { AuthCard, FormError } from '@/components/AuthCard'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { useToast } from '@/components/toast'

export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const uid = params.get('uid')
  const token = params.get('token')
  const navigate = useNavigate()
  const { toast } = useToast()

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<ApiError | null>(null)
  const [mismatch, setMismatch] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setMismatch(null)

    if (password !== confirm) {
      setMismatch('The two passwords do not match.')
      return
    }
    if (!uid || !token) return

    setSubmitting(true)
    try {
      await confirmPasswordReset({ uid, token, new_password: password })
      toast({ title: 'Password updated. Please log in.', tone: 'success' })
      navigate('/login', { replace: true })
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err
          : new ApiError('Could not reset your password. Try again.', 0),
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (!uid || !token) {
    return (
      <AuthCard
        title="Invalid reset link"
        subtitle="This link is missing information. Request a new one."
      >
        <div className="flex justify-center">
          <Link to="/forgot-password">
            <Button variant="outline">Request a new link</Button>
          </Link>
        </div>
      </AuthCard>
    )
  }

  const topError =
    error && Object.keys(error.fieldErrors).length === 0 ? error.message : null

  return (
    <AuthCard title="Set a new password">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        {topError && <FormError message={topError} />}
        <Input
          label="New password"
          type="password"
          name="new_password"
          autoComplete="new-password"
          required
          hint="At least 8 characters."
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={
            error?.fieldErrors.new_password?.[0] ??
            error?.fieldErrors.token?.[0] ??
            error?.fieldErrors.uid?.[0]
          }
        />
        <Input
          label="Confirm new password"
          type="password"
          name="confirm_password"
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={mismatch ?? undefined}
        />
        <Button type="submit" size="lg" loading={submitting} className="mt-1">
          Update password
        </Button>
      </form>
    </AuthCard>
  )
}
