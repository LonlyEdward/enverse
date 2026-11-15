import { Check } from 'lucide-react'

import { cn } from '@/lib/cn'

interface SelectChipProps {
  label: string
  selected: boolean
  onToggle: () => void
}

/** A toggleable multi-select chip (genres, platforms). */
export function SelectChip({ label, selected, onToggle }: SelectChipProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onToggle}
      className={cn(
        'inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors',
        selected
          ? 'border-brand bg-brand/15 text-brand'
          : 'border-border bg-surface text-fg-muted hover:border-border-strong hover:text-fg',
      )}
    >
      {selected && <Check size={14} aria-hidden="true" />}
      {label}
    </button>
  )
}
