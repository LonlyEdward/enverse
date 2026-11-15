import { MailWarning } from 'lucide-react'
import { useState } from 'react'

import { resendVerification } from '@/api/auth'
import { useAuth } from '@/auth/AuthContext'
import { Button } from './Button'
import { useToast } from './toast'

/** A persistent reminder, shown only to logged-in users whose email is not yet
 *  verified, with a one-click resend. */
export function VerifyEmailBanner() {
  const { status, isVerified } = useAuth()
  const { toast } = useToast()
  const [sending, setSending] = useState(false)

  if (status !== 'authenticated' || isVerified) return null

  async function handleResend() {
    setSending(true)
    try {
      await resendVerification()
      toast({
        title: 'Verification email sent',
        description: 'Check your inbox for the new link.',
        tone: 'success',
      })
    } catch {
      toast({
        title: 'Could not send the email',
        description: 'Please try again in a moment.',
        tone: 'error',
      })
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="border-b border-warning/25 bg-warning/10">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-3 gap-y-2 px-4 py-2.5">
        <MailWarning
          size={18}
          className="shrink-0 text-warning"
          aria-hidden="true"
        />
        <p className="text-sm text-fg">
          Verify your email to save favourites and get notifications.
        </p>
        <Button
          variant="outline"
          size="sm"
          loading={sending}
          onClick={handleResend}
          className="ml-auto"
        >
          Resend email
        </Button>
      </div>
    </div>
  )
}
