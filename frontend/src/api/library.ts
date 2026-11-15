import { rawGet, rawSend } from './client'

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
