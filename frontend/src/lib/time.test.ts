import { describe, expect, it } from 'vitest'

import { timeAgo } from './time'

/** Build an ISO string a given number of milliseconds before now. */
function ago(ms: number): string {
  return new Date(Date.now() - ms).toISOString()
}

const SECOND = 1000
const MINUTE = 60 * SECOND
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

describe('timeAgo', () => {
  it('says "just now" within the last 45 seconds', () => {
    expect(timeAgo(ago(5 * SECOND))).toBe('just now')
  })

  it('reports whole minutes', () => {
    expect(timeAgo(ago(5 * MINUTE))).toBe('5m ago')
  })

  it('reports whole hours', () => {
    expect(timeAgo(ago(3 * HOUR))).toBe('3h ago')
  })

  it('reports whole days up to a week', () => {
    expect(timeAgo(ago(2 * DAY))).toBe('2d ago')
  })

  it('falls back to a short date beyond a week', () => {
    const result = timeAgo(ago(10 * DAY))
    expect(result).not.toContain('ago')
    expect(result).not.toBe('')
  })

  it('returns an empty string for an unparseable value', () => {
    expect(timeAgo('not-a-date')).toBe('')
  })
})
