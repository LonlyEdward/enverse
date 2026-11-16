import { Bell, CalendarDays, Library, Sparkles } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useDashboard } from '@/api/hooks/dashboard'
import type { DashboardEvent } from '@/api/dashboard'
import type { CardItem, ContentSummary } from '@/api/types'
import { useAuth } from '@/auth/AuthContext'
import { ErrorState } from '@/components/ErrorState'
import { EventRow } from '@/components/EventRow'
import { PosterRail } from '@/components/PosterRail'
import { Skeleton } from '@/components/Skeleton'
import { CONTENT_TYPES } from '@/lib/contentTypes'
import { parseLocalDate } from '@/lib/calendar'

/** Map the backend's content summary to the poster card shape, preferring a
 *  release date as the subtitle where there is one. */
function toCard(summary: ContentSummary): CardItem {
  const subtitle = summary.date
    ? parseLocalDate(summary.date).toLocaleDateString(undefined, {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : summary.subtitle
  return {
    content_type: summary.content_type,
    id: summary.id,
    title: summary.title,
    poster_url: summary.poster_url,
    subtitle,
  }
}

interface QuickLink {
  to: string
  label: string
  icon: LucideIcon
  badge?: number
}

function QuickLinks({ unread }: { unread: number }) {
  const links: QuickLink[] = [
    { to: '/library', label: 'Library', icon: Library },
    { to: '/recommendations', label: 'For you', icon: Sparkles },
    { to: '/calendar', label: 'Calendar', icon: CalendarDays },
    { to: '/notifications', label: 'Alerts', icon: Bell, badge: unread },
  ]
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {links.map((link) => {
        const Icon = link.icon
        return (
          <Link
            key={link.to}
            to={link.to}
            className="relative flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3 transition-colors hover:border-border-strong hover:bg-surface-2"
          >
            <Icon size={20} className="text-brand" aria-hidden="true" />
            <span className="text-sm font-medium text-fg">{link.label}</span>
            {link.badge ? (
              <span className="absolute right-3 top-3 flex h-5 min-w-5 items-center justify-center rounded-full bg-brand px-1 text-[11px] font-bold text-on-brand">
                {link.badge > 9 ? '9+' : link.badge}
              </span>
            ) : null}
          </Link>
        )
      })}
    </div>
  )
}

function EventSection({
  title,
  events,
}: {
  title: string
  events: DashboardEvent[]
}) {
  if (events.length === 0) return null
  return (
    <section className="py-2">
      <h2 className="mb-2 text-lg font-semibold text-fg">{title}</h2>
      <div className="divide-y divide-border rounded-xl border border-border">
        {events.map((event, i) => (
          <EventRow
            key={`${event.content_type}-${event.id}-${i}`}
            event={event}
            showDate
          />
        ))}
      </div>
    </section>
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-14 rounded-xl" />
        ))}
      </div>
      {Array.from({ length: 3 }).map((_, row) => (
        <div key={row}>
          <Skeleton className="mb-3 h-6 w-48" />
          <div className="flex gap-4 overflow-hidden">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[2/3] w-32 shrink-0 rounded-xl sm:w-36" />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export function DashboardPage() {
  const { user } = useAuth()
  const { data, isLoading, isError, error, refetch } = useDashboard()

  const name = user?.display_name || 'there'

  if (isError) {
    return (
      <div>
        <h1 className="mb-4 text-2xl font-bold text-fg">
          Welcome back, {name}
        </h1>
        <ErrorState
          title="Could not load your dashboard"
          error={error}
          onRetry={() => void refetch()}
        />
      </div>
    )
  }

  const recCards = (data?.recommendations ?? [])
    .filter((rec) => rec.item)
    .map((rec) => toCard(rec.item as ContentSummary))

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-fg">Welcome back, {name}</h1>
        <p className="mt-1 text-sm text-fg-muted">
          Everything you follow and what is landing next.
        </p>
      </div>

      {isLoading ? (
        <DashboardSkeleton />
      ) : (
        <>
          <QuickLinks unread={data?.unread_notifications ?? 0} />

          <EventSection
            title="Your fixtures"
            events={data?.my_fixtures ?? []}
          />
          <EventSection
            title="Updates from your library"
            events={data?.favorites_updates ?? []}
          />

          {recCards.length > 0 && (
            <PosterRail
              title="Recommended for you"
              accent="var(--brand)"
              items={recCards}
              viewAllTo="/recommendations"
            />
          )}

          <PosterRail
            title="In cinemas"
            accent={CONTENT_TYPES.movie.color}
            items={(data?.in_cinemas ?? []).map(toCard)}
            viewAllTo="/movies?status=now_showing"
          />
          <PosterRail
            title="Upcoming movies"
            accent={CONTENT_TYPES.movie.color}
            items={(data?.upcoming_movies ?? []).map(toCard)}
            viewAllTo="/movies?status=upcoming"
          />
          <PosterRail
            title="Upcoming TV"
            accent={CONTENT_TYPES.tv.color}
            items={(data?.upcoming_tv ?? []).map(toCard)}
            viewAllTo="/tv"
          />
          <PosterRail
            title="Anime airing now"
            accent={CONTENT_TYPES.anime.color}
            items={(data?.anime_airing ?? []).map(toCard)}
            viewAllTo="/anime"
          />
          <PosterRail
            title="Upcoming games"
            accent={CONTENT_TYPES.game.color}
            items={(data?.upcoming_games ?? []).map(toCard)}
            viewAllTo="/games?status=upcoming"
          />
        </>
      )}
    </div>
  )
}
