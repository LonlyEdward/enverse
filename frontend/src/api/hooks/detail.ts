import { useQuery } from '@tanstack/react-query'

import { rawGet } from '../client'

const PATH: Record<string, string> = {
  movie: 'movies',
  tv: 'tv',
  anime: 'anime',
  game: 'games',
}

/** Fetch a catalogue item's full detail (public endpoint). The shape varies by
 *  type, so callers read it loosely. */
export function useDetail(contentType: string, id: string | undefined) {
  const segment = PATH[contentType]
  return useQuery({
    queryKey: ['detail', contentType, id],
    queryFn: () => rawGet<Record<string, unknown>>(`/api/v1/${segment}/${id}/`),
    enabled: Boolean(segment && id),
  })
}

/** Fetch a football team's detail, including next fixtures and recent results. */
export function useTeamDetail(id: string | undefined) {
  return useQuery({
    queryKey: ['team-detail', id],
    queryFn: () =>
      rawGet<Record<string, unknown>>(`/api/v1/football/teams/${id}/`),
    enabled: Boolean(id),
  })
}
