import { Bell } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import type { NotificationItem } from '@/api/notifications'
import {
  useMarkAllRead,
  useMarkRead,
  useNotifications,
  useUnreadCount,
} from '@/api/hooks/notifications'
import { ErrorState } from './ErrorState'
import { NotificationRow } from './NotificationRow'
import { Spinner } from './Spinner'

/** Bell with an unread badge and a dropdown of the most recent notifications.
 *  Only mounted for authenticated users (the TopBar decides). */
export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const countQuery = useUnreadCount(true)
  const unread = countQuery.data ?? 0

  // Only fetch the list while the panel is open; the badge polls on its own.
  const listQuery = useNotifications({})
  const markRead = useMarkRead()
  const markAllRead = useMarkAllRead()

  // Close on outside click or Escape.
  useEffect(() => {
    if (!open) return
    function onPointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false)
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  function handleOpenItem(notification: NotificationItem) {
    if (!notification.is_read) markRead.mutate(notification.id)
    setOpen(false)
  }

  const recent = listQuery.data?.results.slice(0, 6) ?? []

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={
          unread > 0 ? `Notifications, ${unread} unread` : 'Notifications'
        }
        aria-expanded={open}
        aria-haspopup="true"
        className="relative flex h-10 w-10 items-center justify-center rounded-lg text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg"
      >
        <Bell size={18} aria-hidden="true" />
        {unread > 0 && (
          <span
            className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand px-1 text-[10px] font-bold leading-none text-on-brand"
            aria-hidden="true"
          >
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Notifications"
          className="absolute right-0 top-12 z-50 w-[22rem] max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border border-border bg-surface shadow-[var(--shadow-pop)]"
        >
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <h2 className="text-sm font-semibold text-fg">Notifications</h2>
            {unread > 0 && (
              <button
                type="button"
                onClick={() => markAllRead.mutate()}
                disabled={markAllRead.isPending}
                className="cursor-pointer text-xs font-medium text-brand hover:underline disabled:opacity-60"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="max-h-[22rem] overflow-y-auto">
            {listQuery.isLoading ? (
              <div className="flex justify-center py-10">
                <Spinner label="Loading notifications" size={18} />
              </div>
            ) : listQuery.isError ? (
              <ErrorState
                error={listQuery.error}
                onRetry={() => void listQuery.refetch()}
              />
            ) : recent.length === 0 ? (
              <p className="px-4 py-10 text-center text-sm text-fg-muted">
                You are all caught up.
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {recent.map((notification) => (
                  <li key={notification.id}>
                    <NotificationRow
                      notification={notification}
                      onOpen={handleOpenItem}
                      compact
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>

          <Link
            to="/notifications"
            onClick={() => setOpen(false)}
            className="block border-t border-border px-4 py-3 text-center text-sm font-medium text-fg-muted hover:bg-surface-2 hover:text-fg"
          >
            See all notifications
          </Link>
        </div>
      )}
    </div>
  )
}
