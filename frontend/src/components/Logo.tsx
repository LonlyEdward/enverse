import { Link } from 'react-router-dom'

import { cn } from '@/lib/cn'

/** The EnVerse brand logo: the hexagon play-mark (shipped as an SVG asset in
 *  /public/logos) beside the wordmark. The mark's gradient reads on any
 *  background, and the wordmark is themed text so "En" stays legible in both
 *  light and dark — the shipped full-logo image is dark-only. */
export function Logo({ className }: { className?: string }) {
  return (
    <Link
      to="/"
      aria-label="EnVerse home"
      className={cn(
        'inline-flex items-center gap-2 rounded-md focus-visible:outline-none',
        className,
      )}
    >
      <img
        src="/logos/enverse-logo-icon.svg"
        alt=""
        width={120}
        height={120}
        className="h-8 w-8"
      />
      <span className="font-display text-xl font-bold tracking-tight">
        <span className="text-fg">En</span>
        <span className="text-brand">Verse</span>
      </span>
    </Link>
  )
}
