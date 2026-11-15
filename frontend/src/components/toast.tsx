import { CheckCircle2, Info, TriangleAlert, X } from 'lucide-react'
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from 'react'
import type { ReactNode } from 'react'

import { cn } from '@/lib/cn'

type ToastTone = 'info' | 'success' | 'error'

interface Toast {
  id: number
  title: string
  description?: string
  tone: ToastTone
}

interface ToastInput {
  title: string
  description?: string
  tone?: ToastTone
}

interface ToastContextValue {
  toast: (input: ToastInput) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

const TONE_ICON = {
  info: Info,
  success: CheckCircle2,
  error: TriangleAlert,
} as const

const TONE_COLOR: Record<ToastTone, string> = {
  info: 'text-info',
  success: 'text-success',
  error: 'text-danger',
}

const DISMISS_MS = 5000

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const nextId = useRef(0)

  const remove = useCallback((id: number) => {
    setToasts((current) => current.filter((t) => t.id !== id))
  }, [])

  const toast = useCallback(
    ({ title, description, tone = 'info' }: ToastInput) => {
      const id = nextId.current++
      setToasts((current) => [...current, { id, title, description, tone }])
      window.setTimeout(() => remove(id), DISMISS_MS)
    },
    [remove],
  )

  const value = useMemo(() => ({ toast }), [toast])

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex flex-col items-center gap-2 p-4 sm:bottom-4 sm:right-4 sm:left-auto sm:items-end"
        aria-live="polite"
        aria-atomic="false"
      >
        {toasts.map((t) => {
          const Icon = TONE_ICON[t.tone]
          return (
            <div
              key={t.id}
              role={t.tone === 'error' ? 'alert' : 'status'}
              className={cn(
                'pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl border border-border bg-surface px-4 py-3 shadow-[var(--shadow-pop)]',
              )}
            >
              <Icon
                size={18}
                className={cn('mt-0.5 shrink-0', TONE_COLOR[t.tone])}
                aria-hidden="true"
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-fg">{t.title}</p>
                {t.description && (
                  <p className="mt-0.5 text-sm text-fg-muted">
                    {t.description}
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={() => remove(t.id)}
                aria-label="Dismiss notification"
                className="cursor-pointer rounded p-0.5 text-fg-subtle hover:text-fg"
              >
                <X size={16} aria-hidden="true" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within a ToastProvider')
  return ctx
}
