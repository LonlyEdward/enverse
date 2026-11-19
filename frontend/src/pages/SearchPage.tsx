import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { searchContent } from '@/api/preferences'
import { POSTER_GRID } from '@/lib/grid'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { Input } from '@/components/Input'
import { PosterCard } from '@/components/PosterCard'
import { PosterSkeleton } from '@/components/Skeleton'
import { CONTENT_TYPE_ORDER, CONTENT_TYPES } from '@/lib/contentTypes'
import { useDebouncedValue } from '@/lib/useDebouncedValue'

export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const [term, setTerm] = useState(params.get('q') ?? '')
  const debounced = useDebouncedValue(term.trim(), 300)
  const enabled = debounced.length >= 2

  // Keep the URL in step with the debounced query so searches are shareable.
  useEffect(() => {
    setParams(debounced ? { q: debounced } : {}, { replace: true })
  }, [debounced, setParams])

  const query = useQuery({
    queryKey: ['search', debounced],
    queryFn: () => searchContent(debounced),
    enabled,
  })

  const groups = CONTENT_TYPE_ORDER.map((type) => ({
    type,
    items: (query.data ?? []).filter((r) => r.content_type === type),
  })).filter((g) => g.items.length > 0)

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="mb-4 text-2xl font-bold text-fg">Search</h1>
      <Input
        label="Search EnVerse"
        hideLabel
        autoFocus
        placeholder="Search movies, TV, anime, games and teams"
        leftIcon={<Search size={18} aria-hidden="true" />}
        value={term}
        onChange={(e) => setTerm(e.target.value)}
      />

      <div className="mt-8">
        {!enabled && (
          <p className="py-10 text-center text-sm text-fg-subtle">
            Type at least two characters to search.
          </p>
        )}

        {enabled && query.isError && (
          <ErrorState
            error={query.error}
            onRetry={() => void query.refetch()}
          />
        )}

        {enabled && query.isLoading && (
          <div className={POSTER_GRID}>
            {Array.from({ length: 12 }).map((_, i) => (
              <PosterSkeleton key={i} />
            ))}
          </div>
        )}

        {enabled && query.data && groups.length === 0 && (
          <EmptyState
            title={`No results for “${debounced}”`}
            description="Try a different title, or check your spelling."
          />
        )}

        <div className="space-y-10">
          {groups.map(({ type, items }) => {
            const meta = CONTENT_TYPES[type]
            return (
              <section key={type}>
                <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-fg">
                  <span
                    className="h-4 w-1 rounded-full"
                    style={{ backgroundColor: meta.color }}
                    aria-hidden="true"
                  />
                  {meta.plural}
                </h2>
                <div className={POSTER_GRID}>
                  {items.map((item) => (
                    <PosterCard
                      key={`${item.content_type}-${item.id}`}
                      item={item}
                    />
                  ))}
                </div>
              </section>
            )
          })}
        </div>
      </div>
    </div>
  )
}
