import { cn } from '@/lib/cn'

/** A shimmering placeholder block. Reserve the real element's size with the
 *  className to avoid layout shift when content arrives. */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-surface-2', className)}
      aria-hidden="true"
    />
  )
}

/** A poster-shaped skeleton (2:3) matching PosterCard, for loading rails. */
export function PosterSkeleton() {
  return (
    <div className="w-full">
      <Skeleton className="aspect-[2/3] w-full rounded-xl" />
      <Skeleton className="mt-2 h-4 w-4/5" />
      <Skeleton className="mt-1.5 h-3 w-2/5" />
    </div>
  )
}
