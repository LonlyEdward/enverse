import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import { listLibrary, removeFromList } from '../library'
import type { LibraryRow, ListKind } from '../library'

/** A page of one library list. */
export function useLibraryList(
  kind: ListKind,
  contentType: string,
  page: number,
) {
  return useQuery({
    queryKey: ['library', kind, contentType, page],
    queryFn: () => listLibrary(kind, contentType || undefined, page),
  })
}

/** Remove a saved item, then refresh both the list and that item's button
 *  state (so a detail page's toggle reflects the change). */
export function useRemoveFromLibrary(kind: ListKind) {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (row: LibraryRow) => removeFromList(kind, row.id),
    onSuccess: (_data, row) => {
      void client.invalidateQueries({ queryKey: ['library', kind] })
      void client.invalidateQueries({
        queryKey: ['lib-status', row.content_type, row.object_id],
      })
    },
  })
}
