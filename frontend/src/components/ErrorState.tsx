import { TriangleAlert } from 'lucide-react'

import { ApiError } from '@/api/errors'
import { Button } from './Button'

interface ErrorStateProps {
  title?: string
  error?: unknown
  onRetry?: () => void
}

function messageFor(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Something went wrong. Please try again.'
}

/** Shown when a data view fails to load. Explains what happened and offers a
 *  way forward, in the interface's own voice. */
export function ErrorState({
  title = 'Could not load this',
  error,
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center"
      role="alert"
    >
      <span className="flex h-14 w-14 items-center justify-center rounded-full bg-danger/15 text-danger">
        <TriangleAlert size={26} aria-hidden="true" />
      </span>
      <h2 className="text-lg font-semibold text-fg">{title}</h2>
      <p className="max-w-sm text-sm text-fg-muted">{messageFor(error)}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-2">
          Try again
        </Button>
      )}
    </div>
  )
}
