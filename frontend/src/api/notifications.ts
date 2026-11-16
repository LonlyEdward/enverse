import { rawGet, rawSend } from './client'
import type { ContentSummary } from './types'

/** The three event kinds the backend emits. */
export type NotificationKind = 'release' | 'schedule' | 'update'

/** One in-app notification row, with the referenced item summarised inline.
 *  `item` can be null when the content it pointed at has since been removed. */
export interface NotificationItem {
  id: number
  kind: NotificationKind
  content_type: string
  object_id: number
  title: string
  body: string
  created_at: string
  read_at: string | null
  is_read: boolean
  item: ContentSummary | null
}

export interface NotificationPage {
  count: number
  next: string | null
  previous: string | null
  results: NotificationItem[]
}

export interface NotificationQuery {
  unread?: boolean
  kind?: NotificationKind
  page?: number
}

/** The user's in-app feed, newest first. Paginated. */
export function listNotifications(
  query: NotificationQuery = {},
): Promise<NotificationPage> {
  const params = new URLSearchParams()
  if (query.unread) params.set('unread', 'true')
  if (query.kind) params.set('kind', query.kind)
  if (query.page) params.set('page', String(query.page))
  const qs = params.toString()
  return rawGet<NotificationPage>(`/api/v1/notifications/${qs ? `?${qs}` : ''}`)
}

/** How many in-app notifications are still unread. */
export async function getUnreadCount(): Promise<number> {
  const data = await rawGet<{ count: number }>(
    '/api/v1/notifications/unread-count/',
  )
  return data.count ?? 0
}

/** Mark one notification read (idempotent). */
export async function markRead(id: number): Promise<void> {
  await rawSend('POST', `/api/v1/notifications/${id}/read/`)
}

/** Mark every unread notification read; returns how many changed. */
export async function markAllRead(): Promise<number> {
  const data = await rawSend<{ marked_read: number }>(
    'POST',
    '/api/v1/notifications/read-all/',
  )
  return data?.marked_read ?? 0
}

/** Delete one of the user's own notifications. */
export async function deleteNotification(id: number): Promise<void> {
  await rawSend('DELETE', `/api/v1/notifications/${id}/`)
}
