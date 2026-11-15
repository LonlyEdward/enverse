import { useQuery } from '@tanstack/react-query'

import { api } from '../client'
import { unwrap } from '../errors'
import type { CardItem, CardPage } from '../types'

// --- mapping --------------------------------------------------------------
function prettify(value?: string): string | undefined {
  if (!value) return undefined
  return value
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

function toCard(raw: Record<string, unknown>): CardItem {
  const date = (raw.release_date ?? raw.first_air_date ?? raw.start_date) as
    string | null | undefined
  const year = typeof date === 'string' ? date.slice(0, 4) : undefined
  const status =
    typeof raw.airing_status === 'string'
      ? (raw.airing_status as string)
      : typeof raw.status === 'string'
        ? (raw.status as string)
        : undefined
  return {
    content_type: String(raw.content_type),
    id: Number(raw.id),
    title: String(raw.title),
    poster_url: typeof raw.poster_url === 'string' ? raw.poster_url : undefined,
    subtitle: year ?? prettify(status),
  }
}

function toPage(data: unknown): CardPage {
  const d = data as {
    count?: number
    next?: string | null
    previous?: string | null
    results?: unknown[]
  }
  return {
    count: d.count ?? 0,
    next: d.next ?? null,
    previous: d.previous ?? null,
    results: (d.results ?? []).map((x) => toCard(x as Record<string, unknown>)),
  }
}

// --- catalogue lists ------------------------------------------------------
export interface MovieQuery {
  status?: 'now_showing' | 'recent' | 'upcoming'
  genre?: string
  year?: number
  rating_gte?: number
  ordering?: string
  page?: number
  page_size?: number
}

export function useMovies(query: MovieQuery) {
  return useQuery({
    queryKey: ['movies', query],
    queryFn: async () =>
      toPage(unwrap(await api.GET('/api/v1/movies/', { params: { query } }))),
  })
}

export interface TVQuery {
  status?: 'canceled' | 'ended' | 'returning'
  genre?: string
  rating_gte?: number
  ordering?: string
  page?: number
  page_size?: number
}

export function useTV(query: TVQuery) {
  return useQuery({
    queryKey: ['tv', query],
    queryFn: async () =>
      toPage(unwrap(await api.GET('/api/v1/tv/', { params: { query } }))),
  })
}

export interface AnimeQuery {
  airing_status?:
    'cancelled' | 'finished' | 'hiatus' | 'not_yet_released' | 'releasing'
  genre?: string
  season?: 'fall' | 'spring' | 'summer' | 'winter'
  rating_gte?: number
  ordering?: string
  page?: number
  page_size?: number
}

export function useAnime(query: AnimeQuery) {
  return useQuery({
    queryKey: ['anime', query],
    queryFn: async () =>
      toPage(unwrap(await api.GET('/api/v1/anime/', { params: { query } }))),
  })
}

export interface GameQuery {
  status?: 'released' | 'upcoming'
  genre?: string
  platform?: string
  rating_gte?: number
  ordering?: string
  page?: number
  page_size?: number
}

export function useGames(query: GameQuery) {
  return useQuery({
    queryKey: ['games', query],
    queryFn: async () =>
      toPage(unwrap(await api.GET('/api/v1/games/', { params: { query } }))),
  })
}

// --- football -------------------------------------------------------------
export interface FixtureQuery {
  competition?: string
  status?: 'cancelled' | 'finished' | 'live' | 'postponed' | 'scheduled'
  team?: number
  date_from?: string
  date_to?: string
  ordering?: string
  page?: number
  page_size?: number
}

export function useFixtures(query: FixtureQuery) {
  return useQuery({
    queryKey: ['fixtures', query],
    queryFn: async () =>
      unwrap(
        await api.GET('/api/v1/football/fixtures/', { params: { query } }),
      ) as unknown as {
        count: number
        next: string | null
        previous: string | null
        results: FixtureRow[]
      },
  })
}

export interface TeamRow {
  id: number
  name: string
  logo_url: string
  competition: string
}

export function useTeams(search: string, page = 1) {
  return useQuery({
    queryKey: ['teams', search, page],
    queryFn: async () =>
      unwrap(
        await api.GET('/api/v1/football/teams/', {
          params: { query: { search, page } },
        }),
      ) as unknown as {
        count: number
        next: string | null
        previous: string | null
        results: TeamRow[]
      },
  })
}

export interface TeamRef {
  id: number
  name: string
  logo_url: string
}

export interface FixtureRow {
  id: number
  competition: string
  round: string
  venue: string
  kickoff_at: string
  status: string
  home_team: TeamRef
  away_team: TeamRef
  home_score: number | null
  away_score: number | null
}
