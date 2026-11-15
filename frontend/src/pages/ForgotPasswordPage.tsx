import { MailCheck } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { requestPasswordReset } from '@/api/auth'
import { AuthCard } from '@/components/AuthCard'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    try {
      await requestPasswordReset(email)
    } catch {
      // The endpoint never reveals whether the account exists; even on an
      // unexpected error we show the same neutral confirmation.
    } finally {
      setSubmitting(false)
      setSent(true)
    }
  }

  if (sent) {
    return (
      <AuthCard
        title="Check your inbox"
        subtitle="If an account exists for that email, a reset link is on its way."
      >
        <div className="flex flex-col items-center gap-4 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-success/15 text-success">
            <MailCheck size={26} aria-hidden="true" />
          </span>
          <Link to="/login">
            <Button variant="outline">Back to login</Button>
          </Link>
        </div>
      </AuthCard>
    )
  }

  return (
    <AuthCard
      title="Reset your password"
      subtitle="Enter your email and we'll send a link to set a new password."
      footer={
        <Link to="/login" className="font-medium text-brand hover:underline">
          Back to login
        </Link>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        <Input
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Button type="submit" size="lg" loading={submitting} className="mt-1">
          Send reset link
        </Button>
      </form>
    </AuthCard>
  )
}
