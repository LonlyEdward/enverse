import { cn } from '@/lib/cn'

export interface FilterOption {
  value: string
  label: string
}

interface FilterBarProps {
  options: FilterOption[]
  value: string
  onChange: (value: string) => void
  /** Accessible label for the group of filters. */
  label: string
}

/** A horizontal row of single-select filter chips. Scrolls on small screens
 *  instead of wrapping, so it stays one predictable line. */
export function FilterBar({ options, value, onChange, label }: FilterBarProps) {
  return (
    <div
      role="group"
      aria-label={label}
      className="-mx-1 flex gap-2 overflow-x-auto px-1 py-1"
    >
      {options.map((option) => {
        const active = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(option.value)}
            className={cn(
              'shrink-0 cursor-pointer rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors',
              active
                ? 'border-brand bg-brand/15 text-brand'
                : 'border-border bg-surface text-fg-muted hover:border-border-strong hover:text-fg',
            )}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
