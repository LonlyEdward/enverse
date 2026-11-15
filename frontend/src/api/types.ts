import type { components } from './schema'

export type User = components['schemas']['User']
export type ContentType = components['schemas']['ContentTypeEnum']

/** The minimal fields a poster card needs. Both the summary returned by
 *  trending/search and the richer list rows map onto this. */
export interface CardItem {
  content_type: string
  id: number
  title: string
  poster_url?: string
  subtitle?: string
}

/** The small, uniform item summary the backend returns in lists and rails. */
export interface ContentSummary {
  content_type: string
  id: number
  title: string
  poster_url: string
  date: string | null
  subtitle: string
}

/** A page of results from a paginated list endpoint, mapped to cards. */
export interface CardPage {
  count: number
  next: string | null
  previous: string | null
  results: CardItem[]
}

/** Login and token-refresh responses (the backend returns these as plain
 * dicts, so they are not in the generated schema; typed here by hand). */
export interface AuthTokens {
  access: string
  refresh: string
}

export interface LoginResponse extends AuthTokens {
  user: User
}

/** Shape of /api/v1/trending/ — a rail per content type plus fixtures. */
export interface TrendingResponse {
  movie: ContentSummary[]
  tv: ContentSummary[]
  anime: ContentSummary[]
  game: ContentSummary[]
  football: ContentSummary[]
}
