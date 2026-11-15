import { Inbox } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  title: string
  description?: string
  icon?: LucideIcon
  action?: ReactNode
}

/** Shown when a data view has nothing to show. An empty screen is an
 *  invitation to act, so it guides rather than just reporting emptiness. */
export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-full bg-surface-2 text-fg-subtle">
        <Icon size={26} aria-hidden="true" />
      </span>
      <h2 className="text-lg font-semibold text-fg">{title}</h2>
      {description && (
        <p className="max-w-sm text-sm text-fg-muted">{description}</p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
