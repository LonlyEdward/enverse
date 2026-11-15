import type { ReactNode } from 'react'

import { Logo } from './Logo'

interface AuthCardProps {
  title: string
  subtitle?: string
  children: ReactNode
  footer?: ReactNode
}

/** Shared centred layout for the auth screens (login, register, reset, …). */
export function AuthCard({ title, subtitle, children, footer }: AuthCardProps) {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-sm flex-col justify-center">
      <div className="mb-8 flex flex-col items-center gap-3 text-center">
        <Logo />
        <h1 className="text-2xl font-semibold text-fg">{title}</h1>
        {subtitle && <p className="text-sm text-fg-muted">{subtitle}</p>}
      </div>
      {children}
      {footer && (
        <div className="mt-6 text-center text-sm text-fg-muted">{footer}</div>
      )}
    </div>
  )
}

/** A top-level form error banner (e.g. "wrong password"). */
export function FormError({ message }: { message: string }) {
  return (
    <p
      role="alert"
      className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
    >
      {message}
    </p>
  )
}
