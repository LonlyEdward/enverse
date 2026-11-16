import type { ContentTypeKey } from './contentTypes'

/** Browse/section route for a content type. */
export function sectionPath(type: ContentTypeKey): string {
  switch (type) {
    case 'movie':
      return '/movies'
    case 'tv':
      return '/tv'
    case 'anime':
      return '/anime'
    case 'game':
      return '/games'
    case 'football':
      return '/football'
  }
}

/** Navigation target for a dated feed/notification event. In those feeds a
 *  football event is a *fixture* (two teams, no detail page of its own), so it
 *  lands on the football section rather than being mistaken for a team id.
 *  Everything else goes to its normal detail page. */
export function eventPath(type: string, id: number): string {
  if (type === 'football') return '/football'
  return detailPath(type, id)
}

/** Detail route for a specific item. Football summaries are teams. */
export function detailPath(type: string, id: number): string {
  switch (type) {
    case 'movie':
      return `/movies/${id}`
    case 'tv':
      return `/tv/${id}`
    case 'anime':
      return `/anime/${id}`
    case 'game':
      return `/games/${id}`
    case 'football':
      return `/football/teams/${id}`
    default:
      return '/'
  }
}
