import type { components } from './schema'

export type User = components['schemas']['User']
export type ContentType = components['schemas']['ContentTypeEnum']

/** The small, uniform item summary the backend returns in lists and rails. */
export interface ContentSummary {
  content_type: string
  id: number
  title: string
  poster_url: string
  date: string | null
  subtitle: string
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
