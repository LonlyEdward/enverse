import { CircleCheck, CircleX } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { verifyEmail } from '@/api/auth'
import { ApiError } from '@/api/errors'
import { AuthCard } from '@/components/AuthCard'
import { Button } from '@/components/Button'
import { Spinner } from '@/components/Spinner'

type Status = 'verifying' | 'success' | 'error'

export function VerifyEmailPage() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const [status, setStatus] = useState<Status>(token ? 'verifying' : 'error')
  const [message, setMessage] = useState(
    token ? '' : 'This verification link is missing its token.',
  )
  const ran = useRef(false)

  useEffect(() => {
    // No token is already reflected in the initial state; nothing to do, and
    // the ref guards React StrictMode's double-invoke of the effect.
    if (!token || ran.current) return
    ran.current = true

    verifyEmail(token)
      .then(() => setStatus('success'))
      .catch((err) => {
        setStatus('error')
        setMessage(
          err instanceof ApiError
            ? err.message
            : 'We could not verify this link.',
        )
      })
  }, [token])

  if (status === 'verifying') {
    return (
      <AuthCard title="Verifying your email">
        <div className="flex justify-center py-4">
          <Spinner label="Verifying your email" size={28} />
        </div>
      </AuthCard>
    )
  }

  if (status === 'success') {
    return (
      <AuthCard title="Email verified" subtitle="Your account is ready.">
        <div className="flex flex-col items-center gap-4 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-success/15 text-success">
            <CircleCheck size={26} aria-hidden="true" />
          </span>
          <Link to="/login">
            <Button size="lg">Log in</Button>
          </Link>
        </div>
      </AuthCard>
    )
  }

  return (
    <AuthCard title="Verification failed" subtitle={message}>
      <div className="flex flex-col items-center gap-4 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-danger/15 text-danger">
          <CircleX size={26} aria-hidden="true" />
        </span>
        <p className="text-sm text-fg-muted">
          The link may have expired. Log in and request a new verification
          email.
        </p>
        <Link to="/login">
          <Button variant="outline">Go to login</Button>
        </Link>
      </div>
    </AuthCard>
  )
}
