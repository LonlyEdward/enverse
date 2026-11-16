import { rawGet } from './client'

/** One dated calendar event. Either `date` (a plain release date) or
 *  `datetime` (a timed kickoff/airing, in UTC) is set, never both meaningfully. */
export interface CalendarEvent {
  content_type: string
  id: number
  title: string
  poster_url: string
  kind: 'release' | 'episode' | 'match' | string
  date: string | null
  datetime: string | null
}

export interface CalendarResponse {
  start: string
  end: string
  results: CalendarEvent[]
}

export interface CalendarParams {
  /** Inclusive range, YYYY-MM-DD. The backend caps the span at 62 days. */
  start: string
  end: string
  type?: string
  mine?: boolean
}

/** Dated events across every content type for a date range. */
export function fetchCalendar(params: CalendarParams): Promise<CalendarResponse> {
  const search = new URLSearchParams({ start: params.start, end: params.end })
  if (params.type) search.set('type', params.type)
  if (params.mine) search.set('mine', 'true')
  return rawGet<CalendarResponse>(`/api/v1/calendar/?${search.toString()}`)
}
