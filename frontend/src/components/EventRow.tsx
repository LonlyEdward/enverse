import { useNavigate } from 'react-router-dom'

import type { CalendarEvent } from '@/api/calendar'
import { eventLocalDate, eventTime } from '@/lib/calendar'
import { contentMeta } from '@/lib/contentTypes'
import { eventPath } from '@/lib/routes'

const KIND_LABEL: Record<string, string> = {
  release: 'Release',
  episode: 'Episode',
  match: 'Match',
}

/** A clickable dated-event row shared by the calendar and the dashboard. Shows
 *  a type-coloured bar, the title and a meta line (type · kind · date · time).
 *  Football events are fixtures, so they route to the football section. */
export function EventRow({
  event,
  showDate = false,
}: {
  event: CalendarEvent
  showDate?: boolean
}) {
  const navigate = useNavigate()
  const meta = contentMeta(event.content_type)
  const time = eventTime(event)
  const to = eventPath(event.content_type, event.id)

  const dateStr = showDate
    ? eventLocalDate(event).toLocaleDateString(undefined, {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
      })
    : ''

  const parts = [
    meta?.label ?? event.content_type,
    KIND_LABEL[event.kind] ?? event.kind,
    dateStr,
    time,
  ].filter(Boolean)

  return (
    <button
      type="button"
      onClick={() => to !== '/' && navigate(to)}
      className="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left transition-colors hover:bg-surface-2 focus-visible:bg-surface-2 focus-visible:outline-none"
    >
      <span
        className="h-8 w-1.5 shrink-0 rounded-full"
        style={{ backgroundColor: meta?.color ?? 'var(--brand)' }}
        aria-hidden="true"
      />
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-fg">
          {event.title}
        </span>
        <span className="text-xs text-fg-subtle">{parts.join(' · ')}</span>
      </span>
    </button>
  )
}
