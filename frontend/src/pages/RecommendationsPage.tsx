import { RefreshCw, Sparkles } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'

import { useRecommendations } from '@/api/hooks/recommendations'
import { useRefreshRecommendations } from '@/api/hooks/recommendations'
import type { Recommendation } from '@/api/recommendations'
import { ApiError } from '@/api/errors'
import type { CardItem } from '@/api/types'
import { POSTER_GRID } from '@/lib/grid'
import { Button } from '@/components/Button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { FilterBar } from '@/components/FilterBar'
import type { FilterOption } from '@/components/FilterBar'
import { PosterCard } from '@/components/PosterCard'
import { PosterSkeleton } from '@/components/Skeleton'
import { useToast } from '@/components/toast'

const TYPE_OPTIONS: FilterOption[] = [
  { value: '', label: 'All' },
  { value: 'movie', label: 'Movies' },
  { value: 'tv', label: 'TV' },
  { value: 'anime', label: 'Anime' },
  { value: 'game', label: 'Games' },
]

const GRID = POSTER_GRID

function RecommendationCard({ rec }: { rec: Recommendation }) {
  if (!rec.item) return null
  const card: CardItem = {
    content_type: rec.content_type,
    id: rec.item.id,
    title: rec.item.title,
    poster_url: rec.item.poster_url,
    subtitle: rec.item.subtitle,
  }
  return (
    <div>
      <PosterCard item={card} />
      {rec.reason && (
        <p className="mt-1 flex items-start gap-1 text-xs text-fg-muted">
          <Sparkles
            size={12}
            className="mt-0.5 shrink-0 text-brand"
            aria-hidden="true"
          />
          <span className="line-clamp-2">{rec.reason}</span>
        </p>
      )}
    </div>
  )
}

export function RecommendationsPage() {
  const [params, setParams] = useSearchParams()
  const { toast } = useToast()
  const type = params.get('type') ?? ''

  const query = useRecommendations(type)
  const refresh = useRefreshRecommendations()

  function setType(value: string) {
    const p = new URLSearchParams(params)
    if (value) p.set('type', value)
    else p.delete('type')
    setParams(p)
  }

  function handleRefresh() {
    refresh.mutate(undefined, {
      onSuccess: (count) =>
        toast({
          title: 'Recommendations refreshed',
          description: `${count} picks based on your library.`,
          tone: 'success',
        }),
      onError: (error) => {
        const tooMany = error instanceof ApiError && error.status === 429
        toast({
          title: tooMany ? 'You have refreshed recently' : 'Could not refresh',
          description: tooMany
            ? 'Try again in a little while — this is limited to keep things fast.'
            : 'Please try again.',
          tone: tooMany ? 'info' : 'error',
        })
      },
    })
  }

  const recs = (query.data ?? []).filter((r) => r.item)

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-fg">Recommended for you</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          loading={refresh.isPending}
          leftIcon={<RefreshCw size={16} aria-hidden="true" />}
        >
          Refresh
        </Button>
      </div>

      <p className="mb-5 max-w-prose text-sm text-fg-muted">
        Picks drawn from the genres, platforms and titles in your library. The
        more you save, the sharper they get.
      </p>

      <div className="mb-6">
        <FilterBar
          label="Filter by content type"
          options={TYPE_OPTIONS}
          value={type}
          onChange={setType}
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
      ) : recs.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No recommendations yet"
          description="Favourite a few titles and set your genres, then refresh to see picks made for you."
        />
      ) : (
        <div className={GRID}>
          {recs.map((rec) => (
            <RecommendationCard
              key={`${rec.content_type}-${rec.object_id}`}
              rec={rec}
            />
          ))}
        </div>
      )}
    </div>
  )
}
