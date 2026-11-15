import { Link } from 'react-router-dom'

import { cn } from '@/lib/cn'

/** The EnVerse wordmark: a compact play-mark plus the name. Used in the top
 *  bar and auth pages. */
export function Logo({ className }: { className?: string }) {
  return (
    <Link
      to="/"
      aria-label="EnVerse home"
      className={cn('inline-flex items-center gap-2', className)}
    >
      <span
        aria-hidden="true"
        className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-on-brand"
      >
        <svg width="14" height="14" viewBox="0 0 12 12" fill="currentColor">
          <path d="M2.5 1.2v9.6a.5.5 0 0 0 .77.42l7.1-4.8a.5.5 0 0 0 0-.84l-7.1-4.8a.5.5 0 0 0-.77.42Z" />
        </svg>
      </span>
      <span className="font-display text-lg font-bold tracking-tight">
        <span className="text-fg">En</span>
        <span className="text-brand">Verse</span>
      </span>
    </Link>
  )
}
