import { rawGet } from './client'
import type { CalendarEvent } from './calendar'
import type { ContentSummary } from './types'

/** A dated row in the fixtures / library-updates sections. Structurally a
 *  calendar event (type, id, title, poster, kind, and date or datetime). */
export type DashboardEvent = CalendarEvent

export interface DashboardRecommendation {
  content_type: string
  object_id: number
  reason: string
  item: ContentSummary | null
}

/** The whole personalised home payload, one authenticated call. */
export interface Dashboard {
  in_cinemas: ContentSummary[]
  upcoming_movies: ContentSummary[]
  upcoming_tv: ContentSummary[]
  anime_airing: ContentSummary[]
  upcoming_games: ContentSummary[]
  my_fixtures: DashboardEvent[]
  favorites_updates: DashboardEvent[]
  recommendations: DashboardRecommendation[]
  unread_notifications: number
}

export function fetchDashboard(): Promise<Dashboard> {
  return rawGet<Dashboard>('/api/v1/dashboard/')
}
