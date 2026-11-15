import { Film, Gamepad2, Sparkles, Trophy, Tv } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

/** The five content types EnVerse tracks. `football` appears in the library
 *  and discovery but is a team, not a catalogue title. */
export type ContentTypeKey = 'movie' | 'tv' | 'anime' | 'game' | 'football'

export interface ContentTypeMeta {
  key: ContentTypeKey
  label: string
  /** Plural noun for section headings and tabs. */
  plural: string
  icon: LucideIcon
  /** Tailwind utility backed by the per-type accent CSS variable. */
  text: string
  bg: string
  /** Inline value for dots and borders where a utility will not do. */
  color: string
}

export const CONTENT_TYPES: Record<ContentTypeKey, ContentTypeMeta> = {
  movie: {
    key: 'movie',
    label: 'Movie',
    plural: 'Movies',
    icon: Film,
    text: 'text-movie',
    bg: 'bg-movie',
    color: 'var(--c-movie)',
  },
  tv: {
    key: 'tv',
    label: 'TV',
    plural: 'TV',
    icon: Tv,
    text: 'text-tv',
    bg: 'bg-tv',
    color: 'var(--c-tv)',
  },
  anime: {
    key: 'anime',
    label: 'Anime',
    plural: 'Anime',
    icon: Sparkles,
    text: 'text-anime',
    bg: 'bg-anime',
    color: 'var(--c-anime)',
  },
  game: {
    key: 'game',
    label: 'Game',
    plural: 'Games',
    icon: Gamepad2,
    text: 'text-game',
    bg: 'bg-game',
    color: 'var(--c-game)',
  },
  football: {
    key: 'football',
    label: 'Football',
    plural: 'Football',
    icon: Trophy,
    text: 'text-football',
    bg: 'bg-football',
    color: 'var(--c-football)',
  },
}

/** Stable display order for rails, tabs and legends. */
export const CONTENT_TYPE_ORDER: ContentTypeKey[] = [
  'movie',
  'tv',
  'anime',
  'game',
  'football',
]

export function contentMeta(key: string): ContentTypeMeta | undefined {
  return CONTENT_TYPES[key as ContentTypeKey]
}
