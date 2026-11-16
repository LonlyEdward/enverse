import { CalendarClock, RefreshCw, Sparkles, X } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import type { NotificationItem, NotificationKind } from '@/api/notifications'
import { cn } from '@/lib/cn'
import { contentMeta } from '@/lib/contentTypes'
import { eventPath } from '@/lib/routes'
import { timeAgo } from '@/lib/time'

const KIND_ICON: Record<NotificationKind, LucideIcon> = {
  release: Sparkles,
  schedule: CalendarClock,
  update: RefreshCw,
}

interface NotificationRowProps {
  notification: NotificationItem
  /** Called after navigating, so the opener (dropdown) can close itself. */
  onOpen?: (notification: NotificationItem) => void
  /** When provided, a delete control is shown (full page only). */
  onDelete?: (id: number) => void
  compact?: boolean
}

/** One notification: a type-coloured icon, the message, a relative time and an
 *  unread dot. The whole row is a button that opens the referenced item. */
export function NotificationRow({
  notification,
  onOpen,
  onDelete,
  compact = false,
}: NotificationRowProps) {
  const navigate = useNavigate()
  const meta = contentMeta(notification.content_type)
  const Icon = KIND_ICON[notification.kind] ?? Sparkles
  const accent = meta?.color ?? 'var(--brand)'

  function open() {
    onOpen?.(notification)
    const to = eventPath(notification.content_type, notification.object_id)
    if (to !== '/') navigate(to)
  }

  return (
    <div
      className={cn(
        'group flex items-start gap-3',
        compact ? 'px-3 py-3' : 'px-4 py-4',
        !notification.is_read && 'bg-brand/5',
      )}
    >
      <button
        type="button"
        onClick={open}
        className="flex min-w-0 flex-1 items-start gap-3 text-left focus-visible:outline-none"
      >
        <span
          className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
          style={{
            color: accent,
            backgroundColor: `color-mix(in oklab, ${accent} 16%, transparent)`,
          }}
          aria-hidden="true"
        >
          <Icon size={16} />
        </span>
        <span className="min-w-0 flex-1">
          <span
            className={cn(
              'block text-sm text-fg group-hover:text-brand',
              !notification.is_read && 'font-semibold',
            )}
          >
            {notification.title}
          </span>
          {notification.body && (
            <span className="mt-0.5 block line-clamp-2 text-xs text-fg-muted">
              {notification.body}
            </span>
          )}
          <span className="mt-1 block text-xs text-fg-subtle">
            {timeAgo(notification.created_at)}
          </span>
        </span>
      </button>

      <div className="flex shrink-0 items-center gap-2">
        {!notification.is_read && (
          <span
            className="mt-2 h-2 w-2 rounded-full bg-brand"
            aria-label="Unread"
            role="img"
          />
        )}
        {onDelete && (
          <button
            type="button"
            onClick={() => onDelete(notification.id)}
            aria-label="Delete notification"
            className="cursor-pointer rounded-md p-1 text-fg-subtle opacity-0 transition-opacity hover:bg-surface-2 hover:text-fg focus-visible:opacity-100 group-hover:opacity-100"
          >
            <X size={16} aria-hidden="true" />
          </button>
        )}
      </div>
    </div>
  )
}
