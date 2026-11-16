import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useCalendar } from '@/api/hooks/calendar'
import type { CalendarEvent } from '@/api/calendar'
import { Button } from '@/components/Button'
import { EmptyState } from '@/components/EmptyState'
import { ErrorState } from '@/components/ErrorState'
import { EventRow } from '@/components/EventRow'
import { FilterBar } from '@/components/FilterBar'
import type { FilterOption } from '@/components/FilterBar'
import { Skeleton } from '@/components/Skeleton'
import { cn } from '@/lib/cn'
import { contentMeta } from '@/lib/contentTypes'
import {
  addMonths,
  dayLabel,
  endOfMonth,
  eventDayKey,
  monthGrid,
  monthLabel,
  startOfMonth,
  WEEKDAY_LABELS,
  ymd,
} from '@/lib/calendar'

const TYPE_OPTIONS: FilterOption[] = [
  { value: '', label: 'All' },
  { value: 'movie', label: 'Movies' },
  { value: 'tv', label: 'TV' },
  { value: 'anime', label: 'Anime' },
  { value: 'game', label: 'Games' },
  { value: 'football', label: 'Football' },
]

function MonthView({
  month,
  byDay,
  selected,
  onSelect,
}: {
  month: Date
  byDay: Map<string, CalendarEvent[]>
  selected: string
  onSelect: (key: string) => void
}) {
  const grid = useMemo(() => monthGrid(month), [month])
  const [todayKey] = useState(() => ymd(new Date()))
  const selectedEvents = byDay.get(selected) ?? []

  return (
    <div>
      <div className="overflow-hidden rounded-xl border border-border">
        <div className="grid grid-cols-7 border-b border-border bg-surface-2">
          {WEEKDAY_LABELS.map((label) => (
            <div
              key={label}
              className="px-1 py-2 text-center text-xs font-medium text-fg-subtle"
            >
              <span className="hidden sm:inline">{label}</span>
              <span className="sm:hidden">{label.charAt(0)}</span>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7">
          {grid.flat().map((day) => {
            const key = ymd(day)
            const inMonth = day.getMonth() === month.getMonth()
            const events = byDay.get(key) ?? []
            const isSelected = key === selected
            const isToday = key === todayKey
            return (
              <button
                key={key}
                type="button"
                onClick={() => onSelect(key)}
                aria-pressed={isSelected}
                aria-label={`${dayLabel(day)}, ${events.length} events`}
                className={cn(
                  'flex min-h-14 flex-col items-center gap-1 border-b border-r border-border p-1 transition-colors sm:min-h-20 sm:items-start',
                  inMonth ? 'bg-surface' : 'bg-bg',
                  isSelected && 'ring-2 ring-inset ring-[var(--ring)]',
                  'hover:bg-surface-2 focus-visible:outline-none focus-visible:bg-surface-2',
                )}
              >
                <span
                  className={cn(
                    'flex h-6 w-6 items-center justify-center rounded-full text-xs',
                    inMonth ? 'text-fg' : 'text-fg-subtle',
                    isToday && 'bg-brand font-bold text-on-brand',
                  )}
                >
                  {day.getDate()}
                </span>
                {events.length > 0 && (
                  <span className="flex flex-wrap items-center gap-0.5">
                    {events.slice(0, 4).map((event, i) => (
                      <span
                        key={i}
                        className="h-1.5 w-1.5 rounded-full"
                        style={{
                          backgroundColor:
                            contentMeta(event.content_type)?.color ??
                            'var(--brand)',
                        }}
                        aria-hidden="true"
                      />
                    ))}
                    {events.length > 4 && (
                      <span className="text-[10px] leading-none text-fg-subtle">
                        +{events.length - 4}
                      </span>
                    )}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      <div className="mt-5">
        <h2 className="mb-2 text-sm font-semibold text-fg">
          {dayLabel(new Date(`${selected}T00:00:00`))}
        </h2>
        {selectedEvents.length === 0 ? (
          <p className="rounded-lg border border-border px-3 py-6 text-center text-sm text-fg-muted">
            Nothing scheduled this day.
          </p>
        ) : (
          <div className="divide-y divide-border rounded-lg border border-border">
            {selectedEvents.map((event, i) => (
              <EventRow key={`${event.content_type}-${event.id}-${i}`} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function AgendaView({ byDay }: { byDay: Map<string, CalendarEvent[]> }) {
  const days = [...byDay.keys()].sort()
  if (days.length === 0) {
    return (
      <EmptyState
        icon={CalendarDays}
        title="Nothing scheduled"
        description="No releases or fixtures in this range. Try another month or clear the filters."
      />
    )
  }
  return (
    <div className="space-y-6">
      {days.map((key) => (
        <section key={key}>
          <h2 className="mb-2 text-sm font-semibold text-fg">
            {dayLabel(new Date(`${key}T00:00:00`))}
          </h2>
          <div className="divide-y divide-border rounded-lg border border-border">
            {(byDay.get(key) ?? []).map((event, i) => (
              <EventRow
                key={`${event.content_type}-${event.id}-${i}`}
                event={event}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}

export function CalendarPage() {
  const [month, setMonth] = useState(() => startOfMonth(new Date()))
  const [view, setView] = useState<'month' | 'agenda'>('month')
  const [type, setType] = useState('')
  const [mine, setMine] = useState(false)
  const [selected, setSelected] = useState(() => ymd(new Date()))

  const query = useCalendar({
    start: ymd(startOfMonth(month)),
    end: ymd(endOfMonth(month)),
    type: type || undefined,
    mine,
  })

  const byDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>()
    for (const event of query.data?.results ?? []) {
      const key = eventDayKey(event)
      const list = map.get(key)
      if (list) list.push(event)
      else map.set(key, [event])
    }
    return map
  }, [query.data])

  function changeMonth(delta: number) {
    const next = addMonths(month, delta)
    setMonth(next)
    // Keep the selected day sensible: today if visible, else the 1st.
    const today = new Date()
    setSelected(
      today.getMonth() === next.getMonth() &&
        today.getFullYear() === next.getFullYear()
        ? ymd(today)
        : ymd(next),
    )
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-fg">Calendar</h1>
        <div
          className="flex rounded-lg border border-border p-0.5"
          role="tablist"
          aria-label="Calendar view"
        >
          {(['month', 'agenda'] as const).map((m) => (
            <button
              key={m}
              type="button"
              role="tab"
              aria-selected={view === m}
              onClick={() => setView(m)}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium capitalize transition-colors',
                view === m
                  ? 'bg-surface-3 text-fg'
                  : 'text-fg-muted hover:text-fg',
              )}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => changeMonth(-1)}
            aria-label="Previous month"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg"
          >
            <ChevronLeft size={18} aria-hidden="true" />
          </button>
          <span className="min-w-40 text-center text-base font-semibold text-fg">
            {monthLabel(month)}
          </span>
          <button
            type="button"
            onClick={() => changeMonth(1)}
            aria-label="Next month"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-fg-muted transition-colors hover:bg-surface-2 hover:text-fg"
          >
            <ChevronRight size={18} aria-hidden="true" />
          </button>
        </div>
        <Button
          variant={mine ? 'secondary' : 'outline'}
          size="sm"
          aria-pressed={mine}
          onClick={() => setMine((v) => !v)}
        >
          {mine ? 'My library' : 'Everything'}
        </Button>
      </div>

      <div className="mb-5">
        <FilterBar
          label="Filter by content type"
          options={TYPE_OPTIONS}
          value={type}
          onChange={setType}
        />
      </div>

      {query.isError ? (
        <ErrorState error={query.error} onRetry={() => void query.refetch()} />
      ) : query.isLoading ? (
        <Skeleton className="h-96 w-full rounded-xl" />
      ) : view === 'month' ? (
        <MonthView
          month={month}
          byDay={byDay}
          selected={selected}
          onSelect={setSelected}
        />
      ) : (
        <AgendaView byDay={byDay} />
      )}
    </div>
  )
}
