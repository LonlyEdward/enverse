import { useParams } from 'react-router-dom'

import { useTeamDetail } from '@/api/hooks/detail'
import type { FixtureRow } from '@/api/hooks/lists'
import { ActionBar } from '@/components/ActionBar'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { Skeleton } from '@/components/Skeleton'

function kickoff(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function FixtureLine({ fixture }: { fixture: FixtureRow }) {
  const finished = fixture.status === 'finished'
  return (
    <li className="flex items-center gap-3 rounded-lg border border-border bg-surface px-3 py-2.5 text-sm">
      <span className="min-w-0 flex-1 truncate text-right font-medium text-fg">
        {fixture.home_team.name}
      </span>
      <span className="shrink-0 rounded bg-surface-2 px-2 py-0.5 tabular-nums">
        {finished
          ? `${fixture.home_score ?? 0} – ${fixture.away_score ?? 0}`
          : 'vs'}
      </span>
      <span className="min-w-0 flex-1 truncate font-medium text-fg">
        {fixture.away_team.name}
      </span>
      <time className="hidden shrink-0 text-xs text-fg-subtle sm:block">
        {kickoff(fixture.kickoff_at)}
      </time>
    </li>
  )
}

function FixtureGroup({
  title,
  fixtures,
  empty,
}: {
  title: string
  fixtures: FixtureRow[]
  empty: string
}) {
  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold text-fg">{title}</h2>
      {fixtures.length === 0 ? (
        <p className="text-sm text-fg-subtle">{empty}</p>
      ) : (
        <ul className="space-y-2">
          {fixtures.map((f) => (
            <FixtureLine key={f.id} fixture={f} />
          ))}
        </ul>
      )}
    </section>
  )
}

export function TeamDetailPage() {
  const { id } = useParams()
  const { data, isLoading, isError, error, refetch } = useTeamDetail(id)

  if (isError)
    return <ErrorState error={error} onRetry={() => void refetch()} />
  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full rounded-2xl" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  const team = data as unknown as {
    id: number
    name: string
    logo_url: string
    competition: string
    next_fixtures?: FixtureRow[]
    recent_results?: FixtureRow[]
  }

  if (!team.name) {
    return <EmptyState title="Team not found" />
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-4 rounded-2xl border border-border bg-surface p-5 sm:p-6">
        <img
          src={team.logo_url}
          alt=""
          className="h-16 w-16 rounded-full bg-surface-2 object-contain sm:h-20 sm:w-20"
        />
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold text-fg">{team.name}</h1>
          <p className="text-sm text-fg-muted">{team.competition}</p>
          <div className="mt-4">
            <ActionBar
              contentType="football"
              objectId={team.id ?? Number(id)}
              showWatchlist={false}
            />
          </div>
        </div>
      </div>

      <FixtureGroup
        title="Next fixtures"
        fixtures={team.next_fixtures ?? []}
        empty="No upcoming fixtures scheduled."
      />
      <FixtureGroup
        title="Recent results"
        fixtures={team.recent_results ?? []}
        empty="No recent results yet."
      />
    </div>
  )
}
