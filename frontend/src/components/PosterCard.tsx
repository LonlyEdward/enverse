import { useState } from 'react'
import { Link } from 'react-router-dom'

import type { CardItem } from '@/api/types'
import { cn } from '@/lib/cn'
import { contentMeta } from '@/lib/contentTypes'
import { detailPath } from '@/lib/routes'

/** A poster-first card: the artwork carries the page, with a thin accent rail
 *  marking the content type and the title/subtitle below. */
export function PosterCard({ item }: { item: CardItem }) {
  const [loaded, setLoaded] = useState(false)
  const [broken, setBroken] = useState(false)
  const meta = contentMeta(item.content_type)

  return (
    <Link
      to={detailPath(item.content_type, item.id)}
      className="group block focus-visible:outline-none"
    >
      <div className="relative aspect-[2/3] overflow-hidden rounded-xl bg-surface-2 shadow-[var(--poster-shadow)] ring-1 ring-border transition-transform duration-200 group-hover:-translate-y-1 group-focus-visible:ring-2 group-focus-visible:ring-[var(--ring)]">
        {/* Accent rail marks the content type even before art loads. */}
        {meta && (
          <span
            className="absolute inset-x-0 top-0 z-10 h-1"
            style={{ backgroundColor: meta.color }}
            aria-hidden="true"
          />
        )}

        {!broken && item.poster_url ? (
          <img
            src={item.poster_url}
            alt={item.title}
            loading="lazy"
            decoding="async"
            onLoad={() => setLoaded(true)}
            onError={() => setBroken(true)}
            className={cn(
              'h-full w-full object-cover transition-opacity duration-300',
              loaded ? 'opacity-100' : 'opacity-0',
            )}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center p-3 text-center text-sm text-fg-subtle">
            {item.title}
          </div>
        )}
      </div>

      <div className="mt-2">
        <h3 className="line-clamp-1 text-sm font-medium text-fg group-hover:text-brand">
          {item.title}
        </h3>
        {item.subtitle && (
          <p className="line-clamp-1 text-xs text-fg-subtle">{item.subtitle}</p>
        )}
      </div>
    </Link>
  )
}
