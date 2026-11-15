import { Search } from 'lucide-react'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { useFixtures, useTeams } from '@/api/hooks/lists'
import type { FixtureRow } from '@/api/hooks/lists'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FilterBar } from '@/components/FilterBar'
import { Input } from '@/components/Input'
import { Pagination } from '@/components/Pagination'
import { Skeleton } from '@/components/Skeleton'
import { Spinner } from '@/components/Spinner'
import { useDebouncedValue } from '@/lib/useDebouncedValue'

const TABS = [
  { value: 'fixtures', label: 'Fixtures' },
  { value: 'results', label: 'Results' },
  { value: 'teams', label: 'Teams' },
]

function kickoff(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function FixtureCard({ fixture }: { fixture: FixtureRow }) {
  const finished = fixture.status === 'finished'
  return (
    <li className="flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3">
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs text-fg-subtle">
          {fixture.competition}
          {fixture.round ? ` · ${fixture.round}` : ''}
        </p>
        <div className="mt-1 flex items-center gap-2 text-sm font-medium text-fg">
          <span className="min-w-0 flex-1 truncate text-right">
            {fixture.home_team.name}
          </span>
          <span className="shrink-0 rounded bg-surface-2 px-2 py-0.5 tabular-nums">
            {finished
              ? `${fixture.home_score ?? 0} – ${fixture.away_score ?? 0}`
              : 'vs'}
          </span>
          <span className="min-w-0 flex-1 truncate">
            {fixture.away_team.name}
          </span>
        </div>
      </div>
      <time className="shrink-0 text-right text-xs text-fg-muted">
        {kickoff(fixture.kickoff_at)}
      </time>
    </li>
  )
}

function FixturesList({ status }: { status: 'scheduled' | 'finished' }) {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page') ?? '1') || 1)
  const query = useFixtures({
    status,
    ordering: status === 'finished' ? '-kickoff_at' : 'kickoff_at',
    page,
    page_size: 20,
  })

  function setPage(p: number) {
    const next = new URLSearchParams(params)
    next.set('page', String(p))
    setParams(next)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  if (query.isError)
    return (
      <ErrorState error={query.error} onRetry={() => void query.refetch()} />
    )
  if (query.isLoading) {
    return (
      <ul className="space-y-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-xl" />
        ))}
      </ul>
    )
  }
  const results = query.data?.results ?? []
  if (results.length === 0) {
    return (
      <EmptyState
        title={
          status === 'finished' ? 'No results yet' : 'No upcoming fixtures'
        }
        description="Check back once the schedule is synced."
      />
    )
  }

  const pageCount = query.data
    ? Math.max(1, Math.ceil(query.data.count / 20))
    : 1

  return (
    <>
      <ul className="space-y-2">
        {results.map((f) => (
          <FixtureCard key={f.id} fixture={f} />
        ))}
      </ul>
      <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
    </>
  )
}

function TeamsSearch() {
  const [term, setTerm] = useState('')
  const debounced = useDebouncedValue(term, 300)
  const enabled = debounced.trim().length >= 2
  const teams = useTeams(debounced.trim())

  return (
    <div className="space-y-4">
      <Input
        label="Search teams"
        hideLabel
        placeholder="Search for a club, e.g. Arsenal"
        leftIcon={<Search size={16} aria-hidden="true" />}
        value={term}
        onChange={(e) => setTerm(e.target.value)}
      />
      {!enabled && (
        <p className="py-6 text-center text-sm text-fg-subtle">
          Type at least two characters to search clubs.
        </p>
      )}
      {enabled && teams.isLoading && (
        <div className="flex justify-center py-6">
          <Spinner label="Searching teams" />
        </div>
      )}
      {enabled && teams.data && teams.data.results.length === 0 && (
        <p className="py-4 text-center text-sm text-fg-muted">
          No teams match “{debounced}”.
        </p>
      )}
      <ul className="divide-y divide-border">
        {enabled &&
          teams.data?.results.map((team) => (
            <li key={team.id}>
              <Link
                to={`/football/teams/${team.id}`}
                className="flex items-center gap-3 py-2.5 hover:text-brand"
              >
                <img
                  src={team.logo_url}
                  alt=""
                  className="h-9 w-9 rounded-full bg-surface-2 object-contain"
                  loading="lazy"
                />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-fg">
                    {team.name}
                  </p>
                  <p className="truncate text-xs text-fg-subtle">
                    {team.competition}
                  </p>
                </div>
              </Link>
            </li>
          ))}
      </ul>
    </div>
  )
}

export function FootballPage() {
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') ?? 'fixtures'

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-fg">Football</h1>
      <div className="mb-6">
        <FilterBar
          label="Football view"
          options={TABS}
          value={tab}
          onChange={(v) => setParams(v === 'fixtures' ? {} : { tab: v })}
        />
      </div>

      {tab === 'fixtures' && <FixturesList status="scheduled" />}
      {tab === 'results' && <FixturesList status="finished" />}
      {tab === 'teams' && <TeamsSearch />}
    </div>
  )
}
