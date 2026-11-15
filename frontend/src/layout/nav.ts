import { Compass, Home, LayoutDashboard, Library, Search } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

/** Top-bar links to each catalogue section. */
export const SECTION_LINKS: { to: string; label: string }[] = [
  { to: '/movies', label: 'Movies' },
  { to: '/tv', label: 'TV' },
  { to: '/anime', label: 'Anime' },
  { to: '/games', label: 'Games' },
  { to: '/football', label: 'Football' },
]

export interface TabLink {
  to: string
  label: string
  icon: LucideIcon
  /** Only show this tab when the user is logged in. */
  authOnly?: boolean
}

/** Mobile bottom tabs — kept to five, the usable maximum. */
export const BOTTOM_TABS: TabLink[] = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/movies', label: 'Browse', icon: Compass },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/library', label: 'Library', icon: Library, authOnly: true },
  { to: '/dashboard', label: 'For you', icon: LayoutDashboard, authOnly: true },
]
