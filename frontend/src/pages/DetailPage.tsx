import { Star } from 'lucide-react'
import { useState } from 'react'
import { useParams } from 'react-router-dom'

import { useDetail } from '@/api/hooks/detail'
import type { CardItem } from '@/api/types'
import { ActionBar } from '@/components/ActionBar'
import { Badge, ContentTypeBadge } from '@/components/Badge'
import { ErrorState } from '@/components/ErrorState'
import { PosterRail } from '@/components/PosterRail'
import { Skeleton } from '@/components/Skeleton'
import { cn } from '@/lib/cn'

function str(o: Record<string, unknown>, k: string): string | undefined {
  const v = o[k]
  return typeof v === 'string' && v ? v : undefined
}
function num(o: Record<string, unknown>, k: string): number | undefined {
  const v = o[k]
  return typeof v === 'number' ? v : undefined
}
function arr(o: Record<string, unknown>, k: string): unknown[] {
  const v = o[k]
  return Array.isArray(v) ? v : []
}

interface CastMember {
  name: string
  character?: string
  profile_url?: string
}

/** Privacy-friendly lazy trailer: loads the YouTube iframe only on click, and
 *  from youtube-nocookie. */
function Trailer({ youtubeKey, title }: { youtubeKey: string; title: string }) {
  const [playing, setPlaying] = useState(false)
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-black">
      <div className="relative aspect-video">
        {playing ? (
          <iframe
            className="absolute inset-0 h-full w-full"
            src={`https://www.youtube-nocookie.com/embed/${youtubeKey}?autoplay=1`}
            title={`${title} trailer`}
            allow="accelerated-autoplay; autoplay; encrypted-media; picture-in-picture"
            allowFullScreen
          />
        ) : (
          <button
            type="button"
            onClick={() => setPlaying(true)}
            className="group absolute inset-0 flex items-center justify-center bg-cover bg-center"
            style={{
              backgroundImage: `url(https://i.ytimg.com/vi/${youtubeKey}/hqdefault.jpg)`,
            }}
            aria-label={`Play ${title} trailer`}
          >
            <span className="flex h-16 w-16 items-center justify-center rounded-full bg-brand/90 text-on-brand transition-transform group-hover:scale-110">
              <svg
                width="22"
                height="22"
                viewBox="0 0 12 12"
                fill="currentColor"
              >
                <path d="M2.5 1.2v9.6a.5.5 0 0 0 .77.42l7.1-4.8a.5.5 0 0 0 0-.84l-7.1-4.8a.5.5 0 0 0-.77.42Z" />
              </svg>
            </span>
          </button>
        )}
      </div>
    </div>
  )
}

export function DetailPage({ contentType }: { contentType: string }) {
  const { id } = useParams()
  const { data, isLoading, isError, error, refetch } = useDetail(
    contentType,
    id,
  )

  if (isError) {
    return <ErrorState error={error} onRetry={() => void refetch()} />
  }
  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-64 w-full rounded-2xl" />
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  const title = str(data, 'title') ?? 'Untitled'
  const poster = str(data, 'poster_url')
  const backdrop = str(data, 'backdrop_url') ?? str(data, 'banner_url')
  const overview = str(data, 'description') ?? str(data, 'overview')
  const rating = num(data, 'rating')
  const date =
    str(data, 'release_date') ??
    str(data, 'first_air_date') ??
    str(data, 'start_date')
  const year = date?.slice(0, 4)
  const status = str(data, 'status') ?? str(data, 'airing_status')
  const genres = arr(data, 'genres').filter(
    (g): g is string => typeof g === 'string',
  )
  const trailerKey = str(data, 'trailer_youtube_key')
  const cast = arr(data, 'cast') as CastMember[]
  const similar = arr(data, 'similar') as CardItem[]
  const objectId = num(data, 'id') ?? Number(id)

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-surface">
        {backdrop && (
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-cover bg-center opacity-25"
            style={{ backgroundImage: `url(${backdrop})` }}
          />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/70 to-transparent" />
        <div className="relative flex flex-col gap-6 p-5 sm:flex-row sm:p-8">
          {poster && (
            <img
              src={poster}
              alt={title}
              className="aspect-[2/3] w-40 shrink-0 rounded-xl object-cover shadow-[var(--poster-shadow)] sm:w-52"
            />
          )}
          <div className="min-w-0 flex-1">
            <ContentTypeBadge contentType={contentType} />
            <h1 className="mt-2 text-3xl font-bold text-fg">{title}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-fg-muted">
              {year && <span>{year}</span>}
              {rating != null && (
                <span className="inline-flex items-center gap-1">
                  <Star
                    size={14}
                    className="text-warning"
                    fill="currentColor"
                    aria-hidden="true"
                  />
                  {rating.toFixed(1)}
                </span>
              )}
              {status && (
                <Badge>
                  {status
                    .split('_')
                    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                    .join(' ')}
                </Badge>
              )}
            </div>
            {genres.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {genres.map((g) => (
                  <Badge key={g} tone="neutral">
                    {g}
                  </Badge>
                ))}
              </div>
            )}
            <div className="mt-5">
              <ActionBar contentType={contentType} objectId={objectId} />
            </div>
          </div>
        </div>
      </div>

      {overview && (
        <section>
          <h2 className="mb-2 text-lg font-semibold text-fg">Overview</h2>
          <p className="max-w-3xl text-sm leading-relaxed text-fg-muted">
            {overview}
          </p>
        </section>
      )}

      {trailerKey && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-fg">Trailer</h2>
          <div className="max-w-3xl">
            <Trailer youtubeKey={trailerKey} title={title} />
          </div>
        </section>
      )}

      {cast.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-fg">Cast</h2>
          <div className="flex gap-4 overflow-x-auto pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {cast.slice(0, 12).map((member, i) => (
              <div key={i} className="w-24 shrink-0 text-center">
                <div
                  className={cn(
                    'mx-auto aspect-square w-20 overflow-hidden rounded-full bg-surface-2',
                  )}
                >
                  {member.profile_url && (
                    <img
                      src={member.profile_url}
                      alt=""
                      loading="lazy"
                      className="h-full w-full object-cover"
                    />
                  )}
                </div>
                <p className="mt-1.5 line-clamp-1 text-xs font-medium text-fg">
                  {member.name}
                </p>
                {member.character && (
                  <p className="line-clamp-1 text-xs text-fg-subtle">
                    {member.character}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {similar.length > 0 && (
        <PosterRail title="More like this" items={similar} />
      )}
    </div>
  )
}
