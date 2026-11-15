import { api, rawGet } from './client'
import { unwrap } from './errors'
import type { ContentSummary } from './types'

export type GenreContentType = 'movie' | 'tv' | 'anime' | 'game'

export interface GenrePreferenceItem {
  content_type: GenreContentType
  genre: string
}

export interface FootballTeam {
  id: number
  name: string
  logo_url: string
  competition: string
}

/** Distinct genres available for one content type (public, cached server-side). */
export async function fetchGenres(type: GenreContentType): Promise<string[]> {
  const data = await rawGet<Record<string, string[]>>(
    `/api/v1/meta/genres/?type=${encodeURIComponent(type)}`,
  )
  return data[type] ?? []
}

/** The user's saved genre preferences. */
export async function getGenrePreferences(): Promise<GenrePreferenceItem[]> {
  const data = unwrap(await api.GET('/api/v1/users/me/preferences/genres/'))
  return data.items as GenrePreferenceItem[]
}

/** Replace the user's genre preferences in full. */
export async function saveGenrePreferences(
  items: GenrePreferenceItem[],
): Promise<void> {
  unwrap(
    await api.PUT('/api/v1/users/me/preferences/genres/', { body: { items } }),
  )
}

/** The user's saved platforms. */
export async function getPlatformPreferences(): Promise<string[]> {
  const data = unwrap(
    await api.GET('/api/v1/users/me/preferences/platforms/'),
  ) as { platforms?: string[] }
  return data.platforms ?? []
}

/** Replace the user's platforms in full. */
export async function savePlatformPreferences(
  platforms: string[],
): Promise<void> {
  unwrap(
    await api.PUT('/api/v1/users/me/preferences/platforms/', {
      body: { platforms },
    }),
  )
}

/** Search football teams by name. */
export async function searchTeams(search: string): Promise<FootballTeam[]> {
  const data = unwrap(
    await api.GET('/api/v1/football/teams/', {
      params: { query: { search } },
    }),
  )
  return (data.results ?? []) as unknown as FootballTeam[]
}

/** Follow a football team (idempotent; 201 created / 200 already followed). */
export async function followTeam(teamId: number): Promise<void> {
  unwrap(
    await api.POST('/api/v1/library/following/', {
      body: { content_type: 'football', object_id: teamId },
    }),
  )
}

/** Add any content item to favourites (idempotent). */
export async function addFavorite(
  contentType: ContentSummary['content_type'],
  objectId: number,
): Promise<void> {
  unwrap(
    await api.POST('/api/v1/library/favorites/', {
      body: {
        content_type: contentType as
          'movie' | 'tv' | 'anime' | 'game' | 'football',
        object_id: objectId,
      },
    }),
  )
}

/** Public title/team search for the optional "pick a few favourites" step. */
export async function searchContent(
  q: string,
  type?: string,
): Promise<ContentSummary[]> {
  const params = new URLSearchParams({ q })
  if (type) params.set('type', type)
  const data = await rawGet<{ query: string; results: ContentSummary[] }>(
    `/api/v1/search/?${params.toString()}`,
  )
  return data.results ?? []
}
