import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import {
  deleteNotification,
  getUnreadCount,
  listNotifications,
  markAllRead,
  markRead,
} from '../notifications'
import type { NotificationQuery } from '../notifications'

const COUNT_KEY = ['notifications', 'unread-count']
const LIST_KEY = ['notifications', 'list']

/** The unread badge count. Polls every 60s while the tab is visible, pauses
 *  when it is hidden, and refreshes the moment the tab regains focus. */
export function useUnreadCount(enabled: boolean) {
  return useQuery({
    queryKey: COUNT_KEY,
    queryFn: getUnreadCount,
    enabled,
    refetchInterval: () =>
      document.visibilityState === 'visible' ? 60_000 : false,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    staleTime: 30_000,
  })
}

/** A page of the notification feed. */
export function useNotifications(query: NotificationQuery) {
  return useQuery({
    queryKey: [...LIST_KEY, query],
    queryFn: () => listNotifications(query),
  })
}

/** Invalidate both the feed and the unread badge after a change. */
function useRefreshNotifications() {
  const client = useQueryClient()
  return () => {
    void client.invalidateQueries({ queryKey: LIST_KEY })
    void client.invalidateQueries({ queryKey: COUNT_KEY })
  }
}

export function useMarkRead() {
  const refresh = useRefreshNotifications()
  return useMutation({
    mutationFn: (id: number) => markRead(id),
    onSuccess: refresh,
  })
}

export function useMarkAllRead() {
  const refresh = useRefreshNotifications()
  return useMutation({
    mutationFn: () => markAllRead(),
    onSuccess: refresh,
  })
}

export function useDeleteNotification() {
  const refresh = useRefreshNotifications()
  return useMutation({
    mutationFn: (id: number) => deleteNotification(id),
    onSuccess: refresh,
  })
}
