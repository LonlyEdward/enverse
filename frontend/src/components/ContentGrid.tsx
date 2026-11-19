import type { CardItem } from '@/api/types'
import { POSTER_GRID } from '@/lib/grid'
import { EmptyState } from './EmptyState'
import { ErrorState } from './ErrorState'
import { PosterCard } from './PosterCard'
import { PosterSkeleton } from './Skeleton'

interface ContentGridProps {
  items?: CardItem[]
  isLoading: boolean
  isError: boolean
  error?: unknown
  onRetry?: () => void
  emptyTitle?: string
  emptyDescription?: string
}

const GRID = POSTER_GRID

/** Responsive poster grid with its own loading, empty and error states. */
export function ContentGrid({
  items,
  isLoading,
  isError,
  error,
  onRetry,
  emptyTitle = 'Nothing here yet',
  emptyDescription = 'Try a different filter, or check back soon.',
}: ContentGridProps) {
  if (isError) {
    return <ErrorState error={error} onRetry={onRetry} />
  }

  if (isLoading) {
    return (
      <div className={GRID}>
        {Array.from({ length: 18 }).map((_, i) => (
          <PosterSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (!items || items.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />
  }

  return (
    <div className={GRID}>
      {items.map((item) => (
        <PosterCard key={`${item.content_type}-${item.id}`} item={item} />
      ))}
    </div>
  )
}
