import type { ReactNode } from 'react'

import { contentMeta } from '@/lib/contentTypes'
import { cn } from '@/lib/cn'

type Tone = 'neutral' | 'brand' | 'success' | 'warning' | 'danger'

interface BadgeProps {
  children: ReactNode
  tone?: Tone
  className?: string
}

const TONES: Record<Tone, string> = {
  neutral: 'bg-surface-2 text-fg-muted border-border',
  brand: 'bg-brand/15 text-brand border-brand/30',
  success: 'bg-success/15 text-success border-success/30',
  warning: 'bg-warning/15 text-warning border-warning/30',
  danger: 'bg-danger/15 text-danger border-danger/30',
}

const base =
  'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium'

export function Badge({ children, tone = 'neutral', className }: BadgeProps) {
  return <span className={cn(base, TONES[tone], className)}>{children}</span>
}

/** A badge tinted with a content type's own accent colour, with its icon. */
export function ContentTypeBadge({
  contentType,
  className,
}: {
  contentType: string
  className?: string
}) {
  const meta = contentMeta(contentType)
  if (!meta) return null
  const Icon = meta.icon
  return (
    <span
      className={cn(base, className)}
      style={{
        color: meta.color,
        backgroundColor: `color-mix(in oklab, ${meta.color} 16%, transparent)`,
        borderColor: `color-mix(in oklab, ${meta.color} 32%, transparent)`,
      }}
    >
      <Icon size={12} aria-hidden="true" />
      {meta.label}
    </span>
  )
}
