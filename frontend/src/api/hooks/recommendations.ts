import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import {
  listRecommendations,
  refreshRecommendations,
} from '../recommendations'

/** The user's recommendations, optionally filtered by content type. */
export function useRecommendations(type: string) {
  return useQuery({
    queryKey: ['recommendations', type],
    queryFn: () => listRecommendations(type || undefined),
  })
}

/** Recompute recommendations, then refresh the list. The caller handles a 429
 *  (too many refreshes) through the mutation's error. */
export function useRefreshRecommendations() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: () => refreshRecommendations(),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: ['recommendations'] }),
  })
}
