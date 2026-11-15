import { QueryClient } from '@tanstack/react-query'

import { ApiError } from './errors'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000, // content changes slowly; avoid refetch storms
      retry: (failureCount, error) => {
        // Do not retry auth or client errors; they will not fix themselves.
        if (error instanceof ApiError && error.status < 500) return false
        return failureCount < 2
      },
      refetchOnWindowFocus: false,
    },
  },
})
