import { useQuery } from '@tanstack/react-query'

import { fetchCalendar } from '../calendar'
import type { CalendarParams } from '../calendar'

/** Dated events for a range, content type and mine-only toggle. */
export function useCalendar(params: CalendarParams) {
  return useQuery({
    queryKey: ['calendar', params],
    queryFn: () => fetchCalendar(params),
  })
}
