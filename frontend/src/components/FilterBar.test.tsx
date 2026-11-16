import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FilterBar } from './FilterBar'

const OPTIONS = [
  { value: '', label: 'All' },
  { value: 'now_showing', label: 'In cinemas' },
  { value: 'upcoming', label: 'Upcoming' },
]

describe('FilterBar', () => {
  it('marks the active option as pressed', () => {
    render(
      <FilterBar
        label="Status"
        options={OPTIONS}
        value="upcoming"
        onChange={() => {}}
      />,
    )
    expect(screen.getByRole('button', { name: 'Upcoming' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: 'All' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
  })

  it('reports the chosen value on click', async () => {
    const onChange = vi.fn()
    render(
      <FilterBar
        label="Status"
        options={OPTIONS}
        value=""
        onChange={onChange}
      />,
    )
    await userEvent.click(screen.getByRole('button', { name: 'In cinemas' }))
    expect(onChange).toHaveBeenCalledWith('now_showing')
  })

  it('exposes the group label for assistive tech', () => {
    render(
      <FilterBar
        label="Filter by status"
        options={OPTIONS}
        value=""
        onChange={() => {}}
      />,
    )
    expect(
      screen.getByRole('group', { name: 'Filter by status' }),
    ).toBeInTheDocument()
  })
})
