import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import type { CalendarEvent } from '@/api/calendar'
import { EventRow } from './EventRow'

function event(partial: Partial<CalendarEvent>): CalendarEvent {
  return {
    content_type: 'movie',
    id: 1,
    title: 'Demo Movie 1',
    poster_url: '',
    kind: 'release',
    date: '2026-11-16',
    datetime: null,
    ...partial,
  }
}

function LocationProbe() {
  const location = useLocation()
  return <div data-testid="pathname">{location.pathname}</div>
}

function renderRow(e: CalendarEvent, showDate = false) {
  return render(
    <MemoryRouter initialEntries={['/start']}>
      <EventRow event={e} showDate={showDate} />
      <LocationProbe />
    </MemoryRouter>,
  )
}

describe('EventRow', () => {
  it('shows the title and a type · kind meta line', () => {
    renderRow(event({}))
    expect(screen.getByText('Demo Movie 1')).toBeInTheDocument()
    expect(screen.getByText(/Movie · Release/)).toBeInTheDocument()
  })

  it('navigates to the item detail for a catalogue event', async () => {
    renderRow(event({ content_type: 'movie', id: 5 }))
    await userEvent.click(screen.getByRole('button'))
    expect(screen.getByTestId('pathname')).toHaveTextContent('/movies/5')
  })

  it('sends a football fixture to the football section, not a team page', async () => {
    renderRow(
      event({ content_type: 'football', id: 9, kind: 'match', title: 'A vs B' }),
    )
    await userEvent.click(screen.getByRole('button'))
    expect(screen.getByTestId('pathname')).toHaveTextContent('/football')
  })

  it('includes the date in the meta line when showDate is set', () => {
    renderRow(event({ date: '2026-11-16' }), true)
    expect(screen.getByText(/Nov/)).toBeInTheDocument()
  })
})
