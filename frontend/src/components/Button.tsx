import { Loader2 } from 'lucide-react'
import type { ComponentProps, ReactNode } from 'react'

import { cn } from '@/lib/cn'

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ComponentProps<'button'> {
  variant?: Variant
  size?: Size
  loading?: boolean
  leftIcon?: ReactNode
}

const VARIANTS: Record<Variant, string> = {
  primary:
    'bg-brand text-on-brand hover:bg-brand-hover focus-visible:outline-offset-2',
  secondary: 'bg-surface-2 text-fg hover:bg-surface-3 border border-border',
  outline: 'border border-border-strong text-fg hover:bg-surface-2',
  ghost: 'text-fg-muted hover:text-fg hover:bg-surface-2',
  danger: 'bg-danger text-white hover:brightness-110',
}

const SIZES: Record<Size, string> = {
  sm: 'h-9 px-3 text-sm gap-1.5',
  md: 'h-11 px-4 text-sm gap-2',
  lg: 'h-12 px-6 text-base gap-2',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  leftIcon,
  disabled,
  className,
  children,
  type = 'button',
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(
        'inline-flex cursor-pointer items-center justify-center rounded-lg font-medium transition-colors',
        'disabled:cursor-not-allowed disabled:opacity-55',
        SIZES[size],
        VARIANTS[variant],
        className,
      )}
      {...rest}
    >
      {loading ? (
        <Loader2 className="animate-spin" size={18} aria-hidden="true" />
      ) : (
        leftIcon
      )}
      {children}
    </button>
  )
}
