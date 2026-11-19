import { Bookmark, Clock, Heart, Library as LibraryIcon } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'

import { useLibraryList, useRemoveFromLibrary } from '@/api/hooks/library'
import type { LibraryRow, ListKind } from '@/api/library'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FilterBar } from '@/components/FilterBar'
import type { FilterOption } from '@/components/FilterBar'
import { POSTER_GRID } from '@/lib/grid'
import { LibraryCard } from '@/components/LibraryCard'
import { Pagination } from '@/components/Pagination'
import { PosterSkeleton } from '@/components/Skeleton'
import { useToast } from '@/components/toast'

const PAGE_SIZE = 20

interface KindTab {
  value: ListKind
  label: string
  icon: LucideIcon
  empty: string
}

const KIND_TABS: KindTab[] = [
  {
    value: 'favorites',
    label: 'Favourites',
    icon: Heart,
    empty: 'Tap the heart on anything you love to keep it here.',
  },
  {
    value: 'watchlist',
    label: 'Watchlist',
    icon: Clock,
    empty: 'Add films and shows to your watchlist to find them fast.',
  },
  {
    value: 'bookmarks',
    label: 'Bookmarks',
    icon: Bookmark,
    empty: 'Bookmark anything you want to come back to later.',
  },
  {
    value: 'following',
    label: 'Following',
    icon: LibraryIcon,
    empty: 'Follow teams and shows to track their fixtures and releases.',
  },
]

const TYPE_OPTIONS: FilterOption[] = [
  { value: '', label: 'All' },
  { value: 'movie', label: 'Movies' },
  { value: 'tv', label: 'TV' },
  { value: 'anime', label: 'Anime' },
  { value: 'game', label: 'Games' },
  { value: 'football', label: 'Football' },
]

const GRID = POSTER_GRID

function isKind(value: string): value is ListKind {
  return KIND_TABS.some((tab) => tab.value === value)
}

export function LibraryPage() {
  const [params, setParams] = useSearchParams()
  const { toast } = useToast()

  const tabParam = params.get('tab') ?? 'favorites'
  const kind: ListKind = isKind(tabParam) ? tabParam : 'favorites'
  const type = params.get('type') ?? ''
  const page = Math.max(1, Number(params.get('page') ?? '1') || 1)

  const query = useLibraryList(kind, type, page)
  const remove = useRemoveFromLibrary(kind)

  function update(next: Record<string, string>) {
    const p = new URLSearchParams(params)
    for (const [key, value] of Object.entries(next)) {
      if (value) p.set(key, value)
      else p.delete(key)
    }
    if (!('page' in next)) p.delete('page')
    setParams(p)
  }

  function handleRemove(row: LibraryRow) {
    const title = row.item?.title ?? 'Item'
    remove.mutate(row, {
      onSuccess: () => toast({ title: `Removed ${title}`, tone: 'success' }),
      onError: () =>
        toast({
          title: 'Could not remove that',
          description: 'Please try again.',
          tone: 'error',
        }),
    })
  }

  const activeTab = KIND_TABS.find((tab) => tab.value === kind)!
  const rows = query.data?.results
  const pageCount = query.data
    ? Math.max(1, Math.ceil(query.data.count / PAGE_SIZE))
    : 1

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-fg">Your library</h1>

      <div className="mb-3">
        <FilterBar
          label="Choose a list"
          options={KIND_TABS.map((t) => ({ value: t.value, label: t.label }))}
          value={kind}
          onChange={(v) => update({ tab: v, type })}
        />
      </div>
      <div className="mb-6">
        <FilterBar
          label="Filter by content type"
          options={TYPE_OPTIONS}
          value={type}
          onChange={(v) => update({ type: v })}
        />
      </div>

      {query.isError ? (
        <ErrorState error={query.error} onRetry={() => void query.refetch()} />
      ) : query.isLoading ? (
        <div className={GRID}>
          {Array.from({ length: 12 }).map((_, i) => (
            <PosterSkeleton key={i} />
          ))}
        </div>
      ) : !rows || rows.length === 0 ? (
        <EmptyState
          icon={activeTab.icon}
          title={
            type
              ? `Nothing in ${activeTab.label.toLowerCase()} for this type`
              : `No ${activeTab.label.toLowerCase()} yet`
          }
          description={activeTab.empty}
        />
      ) : (
        <div className={GRID}>
          {rows.map((row) => (
            <LibraryCard
              key={row.id}
              row={row}
              onRemove={handleRemove}
              removing={remove.isPending && remove.variables?.id === row.id}
            />
          ))}
        </div>
      )}

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
