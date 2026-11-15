import { useQuery } from '@tanstack/react-query'
import type { UseQueryResult } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import { fetchGenres } from '@/api/preferences'
import type { GenreContentType } from '@/api/preferences'
import type { CardPage } from '@/api/types'
import { ContentGrid } from './ContentGrid'
import { FilterBar } from './FilterBar'
import type { FilterOption } from './FilterBar'
import { Pagination } from './Pagination'

export const PAGE_SIZE = 24

interface CatalogBrowseProps<Q> {
  title: string
  statusTabs?: FilterOption[]
  genreType?: GenreContentType
  buildQuery: (p: { status: string; genre: string; page: number }) => Q
  useList: (q: Q) => UseQueryResult<CardPage, Error>
}

/** Shared browse screen: a title, optional status tabs and genre filter (all
 *  kept in the URL so links are shareable), a poster grid and pagination. */
export function CatalogBrowse<Q>({
  title,
  statusTabs,
  genreType,
  buildQuery,
  useList,
}: CatalogBrowseProps<Q>) {
  const [params, setParams] = useSearchParams()
  const status = params.get('status') ?? ''
  const genre = params.get('genre') ?? ''
  const page = Math.max(1, Number(params.get('page') ?? '1') || 1)

  const genresQuery = useQuery({
    queryKey: ['genres', genreType],
    queryFn: () => (genreType ? fetchGenres(genreType) : Promise.resolve([])),
    enabled: Boolean(genreType),
    staleTime: 10 * 60_000,
  })

  const list = useList(buildQuery({ status, genre, page }))

  function update(next: Record<string, string>) {
    const p = new URLSearchParams(params)
    for (const [k, v] of Object.entries(next)) {
      if (v) p.set(k, v)
      else p.delete(k)
    }
    // Changing a filter resets paging unless we are setting the page itself.
    if (!('page' in next)) p.delete('page')
    setParams(p)
  }

  const genreOptions: FilterOption[] = [
    { value: '', label: 'All genres' },
    ...(genresQuery.data ?? []).map((g) => ({ value: g, label: g })),
  ]

  const pageCount = list.data
    ? Math.max(1, Math.ceil(list.data.count / PAGE_SIZE))
    : 1

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-fg">{title}</h1>

      {statusTabs && statusTabs.length > 0 && (
        <div className="mb-3">
          <FilterBar
            label="Filter by status"
            options={statusTabs}
            value={status}
            onChange={(v) => update({ status: v })}
          />
        </div>
      )}

      {genreType && (
        <div className="mb-6">
          <FilterBar
            label="Filter by genre"
            options={genreOptions}
            value={genre}
            onChange={(v) => update({ genre: v })}
          />
        </div>
      )}

      <ContentGrid
        items={list.data?.results}
        isLoading={list.isLoading}
        isError={list.isError}
        error={list.error}
        onRetry={() => void list.refetch()}
      />

      <Pagination
        page={page}
        pageCount={pageCount}
        onPageChange={(p) => {
          update({ page: String(p) })
          window.scrollTo({ top: 0, behavior: 'smooth' })
        }}
      />
    </div>
  )
}
