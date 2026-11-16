import { Loader2, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import type { LibraryRow } from '@/api/library'
import { cn } from '@/lib/cn'
import { contentMeta } from '@/lib/contentTypes'
import { detailPath } from '@/lib/routes'

interface LibraryCardProps {
  row: LibraryRow
  onRemove: (row: LibraryRow) => void
  removing: boolean
}

/** A poster card for a saved item with a remove control. Mirrors PosterCard's
 *  look, but the remove button sits outside the link so it never navigates. */
export function LibraryCard({ row, onRemove, removing }: LibraryCardProps) {
  const [loaded, setLoaded] = useState(false)
  const [broken, setBroken] = useState(false)
  const item = row.item
  const meta = contentMeta(row.content_type)
  const to = item ? detailPath(row.content_type, item.id) : null

  const poster = (
    <div className="relative aspect-[2/3] overflow-hidden rounded-xl bg-surface-2 shadow-[var(--poster-shadow)] ring-1 ring-border transition-transform duration-200 group-hover:-translate-y-1 group-focus-visible:ring-2 group-focus-visible:ring-[var(--ring)]">
      {meta && (
        <span
          className="absolute inset-x-0 top-0 z-10 h-1"
          style={{ backgroundColor: meta.color }}
          aria-hidden="true"
        />
      )}
      {item && !broken && item.poster_url ? (
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
          {item ? item.title : 'No longer available'}
        </div>
      )}
    </div>
  )

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => onRemove(row)}
        disabled={removing}
        aria-label={item ? `Remove ${item.title}` : 'Remove item'}
        className="absolute right-1.5 top-1.5 z-20 flex h-7 w-7 items-center justify-center rounded-full bg-black/60 text-white backdrop-blur-sm transition-colors hover:bg-black/80 disabled:opacity-60"
      >
        {removing ? (
          <Loader2 size={14} className="animate-spin" aria-hidden="true" />
        ) : (
          <X size={14} aria-hidden="true" />
        )}
      </button>

      {to ? (
        <Link
          to={to}
          className="group block focus-visible:outline-none"
          aria-label={item?.title}
        >
          {poster}
        </Link>
      ) : (
        <div className="group block">{poster}</div>
      )}

      <div className="mt-2">
        <h3 className="line-clamp-1 text-sm font-medium text-fg">
          {item ? item.title : 'Removed content'}
        </h3>
        {item?.subtitle && (
          <p className="line-clamp-1 text-xs text-fg-subtle">{item.subtitle}</p>
        )}
      </div>
    </div>
  )
}
