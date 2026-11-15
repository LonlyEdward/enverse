import { useQuery } from '@tanstack/react-query'

import { api } from '../client'
import { unwrap } from '../errors'
import type { TrendingResponse } from '../types'

/** What is trending across every content type, for the landing rails. */
export function useTrending() {
  return useQuery({
    queryKey: ['trending'],
    queryFn: async (): Promise<TrendingResponse> =>
      unwrap(await api.GET('/api/v1/trending/')) as unknown as TrendingResponse,
  })
}
