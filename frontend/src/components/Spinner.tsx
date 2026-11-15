import { Loader2 } from 'lucide-react'

import { cn } from '@/lib/cn'

interface SpinnerProps {
  label?: string
  className?: string
  size?: number
}

/** An accessible loading indicator. The label is announced to screen readers. */
export function Spinner({
  label = 'Loading',
  className,
  size = 24,
}: SpinnerProps) {
  return (
    <span
      role="status"
      className={cn('inline-flex items-center gap-2', className)}
    >
      <Loader2
        className="animate-spin text-fg-muted"
        size={size}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </span>
  )
}
