import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { CardItem } from '@/api/types'
import { PosterCard } from './PosterCard'
import { PosterSkeleton } from './Skeleton'

interface PosterRailProps {
  title: string
  items?: CardItem[]
  loading?: boolean
  viewAllTo?: string
  /** Accent colour for the heading marker (per content type). */
  accent?: string
}

/** A titled, horizontally scrolling row of posters. The workhorse of the home
 *  page and every section's trending strip. */
export function PosterRail({
  title,
  items,
  loading,
  viewAllTo,
  accent,
}: PosterRailProps) {
  if (!loading && (!items || items.length === 0)) return null

  return (
    <section className="py-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-fg">
          {accent && (
            <span
              className="h-4 w-1 rounded-full"
              style={{ backgroundColor: accent }}
              aria-hidden="true"
            />
          )}
          {title}
        </h2>
        {viewAllTo && (
          <Link
            to={viewAllTo}
            className="flex items-center gap-0.5 text-sm font-medium text-fg-muted hover:text-brand"
          >
            See all
            <ChevronRight size={16} aria-hidden="true" />
          </Link>
        )}
      </div>

      <div className="-mx-4 flex gap-4 overflow-x-auto px-4 pb-2 sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {loading
          ? Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="w-40 shrink-0 sm:w-44">
                <PosterSkeleton />
              </div>
            ))
          : items?.map((item) => (
              <div
                key={`${item.content_type}-${item.id}`}
                className="w-40 shrink-0 sm:w-44"
              >
                <PosterCard item={item} />
              </div>
            ))}
      </div>
    </section>
  )
}
