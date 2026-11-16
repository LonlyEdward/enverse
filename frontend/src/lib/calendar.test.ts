import { describe, expect, it } from 'vitest'

import type { CalendarEvent } from '@/api/calendar'
import {
  addMonths,
  endOfMonth,
  eventDayKey,
  eventLocalDate,
  eventTime,
  monthGrid,
  parseLocalDate,
  startOfMonth,
  ymd,
} from './calendar'

/** A CalendarEvent with sensible defaults; override what a test cares about. */
function event(partial: Partial<CalendarEvent>): CalendarEvent {
  return {
    content_type: 'movie',
    id: 1,
    title: 'Something',
    poster_url: '',
    kind: 'release',
    date: null,
    datetime: null,
    ...partial,
  }
}

describe('ymd', () => {
  it('formats a local date zero-padded', () => {
    expect(ymd(new Date(2026, 0, 5))).toBe('2026-01-05')
    expect(ymd(new Date(2026, 10, 16))).toBe('2026-11-16')
  })
})

describe('parseLocalDate', () => {
  it('parses YYYY-MM-DD as a local calendar day', () => {
    const d = parseLocalDate('2026-11-16')
    expect(d.getFullYear()).toBe(2026)
    expect(d.getMonth()).toBe(10)
    expect(d.getDate()).toBe(16)
  })
})

describe('startOfMonth / endOfMonth', () => {
  it('returns the first and last day of the month', () => {
    const anchor = new Date(2026, 10, 16)
    expect(ymd(startOfMonth(anchor))).toBe('2026-11-01')
    expect(ymd(endOfMonth(anchor))).toBe('2026-11-30')
  })
})

describe('addMonths', () => {
  it('moves forward across a year boundary', () => {
    const next = addMonths(new Date(2026, 10, 1), 2)
    expect(next.getFullYear()).toBe(2027)
    expect(next.getMonth()).toBe(0)
  })

  it('moves backward across a year boundary', () => {
    const prev = addMonths(new Date(2026, 0, 15), -1)
    expect(prev.getFullYear()).toBe(2025)
    expect(prev.getMonth()).toBe(11)
  })
})

describe('monthGrid', () => {
  const grid = monthGrid(new Date(2026, 10, 1))

  it('starts every week on a Sunday', () => {
    expect(grid[0]![0]!.getDay()).toBe(0)
  })

  it('has rows of seven days', () => {
    for (const week of grid) expect(week).toHaveLength(7)
  })

  it('covers every day of the month', () => {
    const keys = grid.flat().map(ymd)
    expect(keys).toContain('2026-11-01')
    expect(keys).toContain('2026-11-30')
  })
})

describe('event date helpers', () => {
  it('buckets a date-only event by its day with no time', () => {
    const e = event({ date: '2026-11-16' })
    expect(eventDayKey(e)).toBe('2026-11-16')
    expect(eventTime(e)).toBe('')
  })

  it('treats a datetime in the datetime field as timed (UTC test zone)', () => {
    const e = event({ datetime: '2026-11-20T13:00:00+00:00' })
    expect(eventDayKey(e)).toBe('2026-11-20')
    expect(eventTime(e)).toMatch(/\d{1,2}:\d{2}/)
  })

  it('also handles a datetime smuggled into the date field', () => {
    // The dashboard puts anime next-airing datetimes in `date`, not `datetime`.
    const e = event({ date: '2026-11-20T13:00:00+00:00' })
    expect(Number.isNaN(eventLocalDate(e).getTime())).toBe(false)
    expect(eventDayKey(e)).toBe('2026-11-20')
    expect(eventTime(e)).toMatch(/\d{1,2}:\d{2}/)
  })

  it('returns an invalid date when nothing is set', () => {
    expect(Number.isNaN(eventLocalDate(event({})).getTime())).toBe(true)
  })
})
