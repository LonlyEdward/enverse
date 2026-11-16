import { rawGet, rawSend } from './client'
import type { ContentSummary } from './types'

/** One recommendation: a scored content item with a short, human reason. */
export interface Recommendation {
  content_type: string
  object_id: number
  score: number
  reason: string
  item: ContentSummary | null
}

/** The user's recommendations, optionally narrowed to one content type.
 *  Computed lazily server-side on first access, then just read. Not paginated. */
export function listRecommendations(
  type?: string,
): Promise<Recommendation[]> {
  const qs = type ? `?type=${encodeURIComponent(type)}` : ''
  return rawGet<Recommendation[]>(`/api/v1/recommendations/${qs}`)
}

/** Recompute recommendations now; returns how many were produced. Tightly
 *  throttled (10/hour): a 429 is expected and handled by the caller. */
export async function refreshRecommendations(): Promise<number> {
  const data = await rawSend<{ recomputed: number }>(
    'POST',
    '/api/v1/recommendations/refresh/',
  )
  return data?.recomputed ?? 0
}
