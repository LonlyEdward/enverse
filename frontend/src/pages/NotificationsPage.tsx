import { BellOff, CheckCheck } from 'lucide-react'
import { useState } from 'react'

import type { NotificationItem, NotificationKind } from '@/api/notifications'
import {
  useDeleteNotification,
  useMarkAllRead,
  useMarkRead,
  useNotifications,
  useUnreadCount,
} from '@/api/hooks/notifications'
import { Button } from '@/components/Button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FilterBar } from '@/components/FilterBar'
import type { FilterOption } from '@/components/FilterBar'
import { NotificationRow } from '@/components/NotificationRow'
import { Pagination } from '@/components/Pagination'
import { Skeleton } from '@/components/Skeleton'

const PAGE_SIZE = 20 // the backend default page size

const STATUS_TABS: FilterOption[] = [
  { value: '', label: 'All' },
  { value: 'unread', label: 'Unread' },
]

const KIND_TABS: FilterOption[] = [
  { value: '', label: 'All types' },
  { value: 'release', label: 'Releases' },
  { value: 'schedule', label: 'Schedules' },
  { value: 'update', label: 'Updates' },
]

export function NotificationsPage() {
  const [status, setStatus] = useState('')
  const [kind, setKind] = useState('')
  const [page, setPage] = useState(1)

  const unreadCount = useUnreadCount(true).data ?? 0

  const query = useNotifications({
    unread: status === 'unread' || undefined,
    kind: (kind || undefined) as NotificationKind | undefined,
    page,
  })
  const markRead = useMarkRead()
  const markAllRead = useMarkAllRead()
  const remove = useDeleteNotification()

  const results = query.data?.results ?? []
  const pageCount = query.data
    ? Math.max(1, Math.ceil(query.data.count / PAGE_SIZE))
    : 1

  function resetTo(update: () => void) {
    update()
    setPage(1)
  }

  function handleOpen(notification: NotificationItem) {
    if (!notification.is_read) markRead.mutate(notification.id)
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-fg">Notifications</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={() => markAllRead.mutate()}
          disabled={unreadCount === 0 || markAllRead.isPending}
          leftIcon={<CheckCheck size={16} aria-hidden="true" />}
        >
          Mark all read
        </Button>
      </div>

      <div className="mb-2">
        <FilterBar
          label="Filter by read state"
          options={STATUS_TABS}
          value={status}
          onChange={(v) => resetTo(() => setStatus(v))}
        />
      </div>
      <div className="mb-5">
        <FilterBar
          label="Filter by type"
          options={KIND_TABS}
          value={kind}
          onChange={(v) => resetTo(() => setKind(v))}
        />
      </div>

      {query.isError ? (
        <ErrorState error={query.error} onRetry={() => void query.refetch()} />
      ) : query.isLoading ? (
        <div className="divide-y divide-border rounded-xl border border-border">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-start gap-3 px-4 py-4">
              <Skeleton className="h-9 w-9 rounded-full" />
              <div className="flex-1">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="mt-2 h-3 w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : results.length === 0 ? (
        <EmptyState
          icon={BellOff}
          title={
            status === 'unread'
              ? 'No unread notifications'
              : 'No notifications yet'
          }
          description="When something you follow is released or scheduled, it shows up here."
        />
      ) : (
        <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border">
          {results.map((notification) => (
            <li key={notification.id}>
              <NotificationRow
                notification={notification}
                onOpen={handleOpen}
                onDelete={(id) => remove.mutate(id)}
              />
            </li>
          ))}
        </ul>
      )}

      <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
    </div>
  )
}
