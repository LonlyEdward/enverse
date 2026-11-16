import { rawGet, rawSend } from './client'
import type { ContentSummary } from './types'

export interface LibraryStatus {
  favorite: boolean
  watchlist: boolean
  bookmark: boolean
  following: boolean
  notifications_enabled: boolean | null
}

/** The four library lists. `following` carries a notifications toggle. */
export type ListKind = 'favorites' | 'watchlist' | 'bookmarks' | 'following'

/** Map a list to the boolean key the status endpoint returns for it. */
export const STATUS_KEY: Record<ListKind, keyof LibraryStatus> = {
  favorites: 'favorite',
  watchlist: 'watchlist',
  bookmarks: 'bookmark',
  following: 'following',
}

/** Button states for one item in one call. */
export function getLibraryStatus(
  contentType: string,
  objectId: number,
): Promise<LibraryStatus> {
  return rawGet<LibraryStatus>(
    `/api/v1/library/status/?content_type=${encodeURIComponent(contentType)}&object_id=${objectId}`,
  )
}

/** Add an item to a list (idempotent; returns the row, including its id). */
export async function addToList(
  kind: ListKind,
  contentType: string,
  objectId: number,
): Promise<{ id: number }> {
  const row = await rawSend<{ id: number }>(
    'POST',
    `/api/v1/library/${kind}/`,
    {
      content_type: contentType,
      object_id: objectId,
    },
  )
  return row ?? { id: 0 }
}

/** Remove a row by its id. */
export async function removeFromList(
  kind: ListKind,
  rowId: number,
): Promise<void> {
  await rawSend('DELETE', `/api/v1/library/${kind}/${rowId}/`)
}

/** One saved library row, with the referenced content summarised inline.
 *  `item` is null when the content it pointed at has since been removed. */
export interface LibraryRow {
  id: number
  content_type: string
  object_id: number
  created_at: string
  item: ContentSummary | null
  /** Only present on `following` rows. */
  notifications_enabled?: boolean | null
}

export interface LibraryPage {
  count: number
  next: string | null
  previous: string | null
  results: LibraryRow[]
}

/** A page of one library list, optionally narrowed to a single content type. */
export function listLibrary(
  kind: ListKind,
  contentType?: string,
  page = 1,
): Promise<LibraryPage> {
  const params = new URLSearchParams({ page: String(page) })
  if (contentType) params.set('content_type', contentType)
  return rawGet<LibraryPage>(`/api/v1/library/${kind}/?${params.toString()}`)
}
