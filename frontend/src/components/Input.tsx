import { useId } from 'react'
import type { ComponentProps, ReactNode } from 'react'

import { cn } from '@/lib/cn'

interface InputProps extends ComponentProps<'input'> {
  label: string
  /** Visually hide the label but keep it for screen readers. */
  hideLabel?: boolean
  error?: string
  hint?: string
  leftIcon?: ReactNode
}

export function Input({
  label,
  hideLabel = false,
  error,
  hint,
  leftIcon,
  id,
  className,
  ...rest
}: InputProps) {
  const autoId = useId()
  const inputId = id ?? autoId
  const hintId = hint ? `${inputId}-hint` : undefined
  const errorId = error ? `${inputId}-error` : undefined

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={inputId}
        className={cn('text-sm font-medium text-fg', hideLabel && 'sr-only')}
      >
        {label}
      </label>

      <div className="relative">
        {leftIcon && (
          <span
            className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-fg-subtle"
            aria-hidden="true"
          >
            {leftIcon}
          </span>
        )}
        <input
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={cn(errorId, hintId) || undefined}
          className={cn(
            'h-11 w-full rounded-lg border bg-surface px-3 text-fg placeholder:text-fg-subtle',
            'transition-colors focus:outline-none focus-visible:outline-2 focus-visible:outline-offset-0',
            leftIcon ? 'pl-9' : undefined,
            error
              ? 'border-danger'
              : 'border-border focus-visible:border-border-strong',
            className,
          )}
          {...rest}
        />
      </div>

      {hint && !error && (
        <p id={hintId} className="text-xs text-fg-subtle">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className="text-xs text-danger" aria-live="polite">
          {error}
        </p>
      )}
    </div>
  )
}
