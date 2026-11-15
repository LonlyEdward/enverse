import { Link } from 'react-router-dom'

import { useTrending } from '@/api/hooks/content'
import type { TrendingResponse } from '@/api/types'
import { Button } from '@/components/Button'
import { ErrorState } from '@/components/ErrorState'
import { PosterRail } from '@/components/PosterRail'
import { useAuth } from '@/auth/AuthContext'
import { CONTENT_TYPES } from '@/lib/contentTypes'
import { sectionPath } from '@/lib/routes'

const RAIL_TYPES = ['movie', 'tv', 'anime', 'game'] as const

function Hero() {
  const { status } = useAuth()
  const authed = status === 'authenticated'

  return (
    <section className="relative overflow-hidden rounded-2xl border border-border bg-surface px-6 py-12 sm:px-10 sm:py-16">
      {/* Soft type-coloured glow, the one deliberate decorative moment. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full opacity-30 blur-3xl"
        style={{
          background:
            'conic-gradient(from 120deg, var(--c-movie), var(--c-tv), var(--c-anime), var(--c-game), var(--c-football), var(--c-movie))',
        }}
      />
      <div className="relative max-w-2xl">
        <h1 className="text-4xl font-bold leading-[1.05] tracking-tight text-fg sm:text-5xl">
          Everything you follow, and when it lands.
        </h1>
        <p className="mt-4 max-w-xl text-base text-fg-muted sm:text-lg">
          EnVerse tracks movies, TV, anime, games and football in one place, and
          tells you what is coming next — so you never miss a release.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link to={authed ? '/dashboard' : '/login'}>
            <Button size="lg">
              {authed ? 'Go to your dashboard' : 'Get started'}
            </Button>
          </Link>
          <Link to="/movies">
            <Button size="lg" variant="outline">
              Browse the catalogue
            </Button>
          </Link>
        </div>

        {/* The five tracked worlds, each in its own accent — the legend doubles
            as the key to the colour system used throughout the app. */}
        <ul className="mt-9 flex flex-wrap gap-x-5 gap-y-2">
          {Object.values(CONTENT_TYPES).map((meta) => {
            const Icon = meta.icon
            return (
              <li
                key={meta.key}
                className="flex items-center gap-1.5 text-sm text-fg-muted"
              >
                <Icon
                  size={15}
                  style={{ color: meta.color }}
                  aria-hidden="true"
                />
                {meta.plural}
              </li>
            )
          })}
        </ul>
      </div>
    </section>
  )
}

export function HomePage() {
  const { data, isLoading, isError, error, refetch } = useTrending()

  return (
    <div className="space-y-2">
      <Hero />

      {isError ? (
        <ErrorState
          title="Could not load trending titles"
          error={error}
          onRetry={() => void refetch()}
        />
      ) : (
        RAIL_TYPES.map((type) => {
          const meta = CONTENT_TYPES[type]
          const items = data?.[type as keyof TrendingResponse]
          return (
            <PosterRail
              key={type}
              title={`Trending ${meta.plural.toLowerCase()}`}
              accent={meta.color}
              loading={isLoading}
              items={items}
              viewAllTo={sectionPath(type)}
            />
          )
        })
      )}
    </div>
  )
}
