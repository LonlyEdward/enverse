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
