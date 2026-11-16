import { useQuery } from '@tanstack/react-query'

import { fetchDashboard } from '../dashboard'

/** The personalised home dashboard. */
export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
  })
}
