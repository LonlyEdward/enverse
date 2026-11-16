import type { CalendarEvent } from '@/api/calendar'

/** Local YYYY-MM-DD for a Date (the browser's own time zone). */
export function ymd(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** Parse a plain YYYY-MM-DD as local midnight (not UTC, which would shift the
 *  day for viewers behind UTC). */
export function parseLocalDate(value: string): Date {
  const [y, m, d] = value.split('-').map(Number)
  return new Date(y ?? 1970, (m ?? 1) - 1, d ?? 1)
}

/** The local calendar day an event falls on: a timed event is converted from
 *  UTC to the browser's zone; a date-only event is taken as-is. */
export function eventLocalDate(event: CalendarEvent): Date {
  if (event.datetime) return new Date(event.datetime)
  if (event.date) return parseLocalDate(event.date)
  return new Date(NaN)
}

/** The day key (YYYY-MM-DD, local) used to bucket events by day. */
export function eventDayKey(event: CalendarEvent): string {
  return ymd(eventLocalDate(event))
}

/** Local HH:MM for a timed event, or '' for a date-only one. */
export function eventTime(event: CalendarEvent): string {
  if (!event.datetime) return ''
  return new Date(event.datetime).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1)
}

export function endOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0)
}

export function addMonths(date: Date, delta: number): Date {
  return new Date(date.getFullYear(), date.getMonth() + delta, 1)
}

export function isSameDay(a: Date, b: Date): boolean {
  return ymd(a) === ymd(b)
}

/** The weeks (Sunday-start) that cover a month, as a grid of Date cells. Cells
 *  spilling into the neighbouring months are included so every week is full. */
export function monthGrid(date: Date): Date[][] {
  const year = date.getFullYear()
  const month = date.getMonth()
  const startDow = new Date(year, month, 1).getDay()
  const daysInMonth = endOfMonth(date).getDate()
  const weeks = Math.ceil((startDow + daysInMonth) / 7)

  const grid: Date[][] = []
  const cursor = new Date(year, month, 1 - startDow)
  for (let w = 0; w < weeks; w++) {
    const row: Date[] = []
    for (let d = 0; d < 7; d++) {
      row.push(new Date(cursor))
      cursor.setDate(cursor.getDate() + 1)
    }
    grid.push(row)
  }
  return grid
}

export const WEEKDAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export function monthLabel(date: Date): string {
  return date.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
}

export function dayLabel(date: Date): string {
  return date.toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
}
