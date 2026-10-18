import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Plan, Stop, Summary } from '../types'
import { KpiRow } from './KpiRow'
import { RoutesPanel } from './RoutesPanel'
import { StopsPanel } from './StopsPanel'

const stop = (over: Partial<Stop> = {}): Stop => ({
  id: 1,
  label: 'Hartford Hospital Lab',
  address: '',
  lat: 41.75,
  lng: -72.68,
  packages: 4,
  priority: false,
  window_start: null,
  window_end: null,
  status: 'assigned',
  ...over,
})

const summary: Summary = {
  depot: { name: 'Cheshire Depot', lat: 41.5, lng: -72.9 },
  drivers_active: 3,
  stops_total: 18,
  stops_by_status: { pending: 2, assigned: 10, in_transit: 1, delivered: 5, failed: 0 },
  packages_pending: 7,
}

const plan: Plan = {
  id: 9,
  solver: 'ortools',
  total_distance_km: 266.3,
  total_duration_min: 409.7,
  unassigned: [],
  created_at: '2026-10-18T12:00:00Z',
  routes: [
    {
      id: 1,
      driver_id: 1,
      driver_name: 'Marcus R.',
      stop_ids: [1],
      distance_km: 40,
      duration_min: 60,
      load: 30,
      capacity: 40,
      path: [],
    },
  ],
}

describe('KpiRow', () => {
  it('shows delivered progress and plan totals', () => {
    render(<KpiRow summary={summary} plan={plan} />)
    expect(screen.getByText('5/18')).toBeInTheDocument()
    expect(screen.getByText('266 km')).toBeInTheDocument()
    expect(screen.getByText('6h 50m drive')).toBeInTheDocument()
  })

  it('handles no plan', () => {
    render(<KpiRow summary={summary} plan={null} />)
    expect(screen.getByText('not optimized')).toBeInTheDocument()
  })
})

describe('StopsPanel', () => {
  it('offers only valid next statuses', () => {
    const onStatus = vi.fn()
    render(<StopsPanel stops={[stop()]} onStatus={onStatus} onDelete={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: 'Start' }))
    expect(onStatus).toHaveBeenCalledWith(1, 'in_transit')
    expect(screen.queryByRole('button', { name: 'Delivered' })).toBeNull()
  })

  it('hides delete while in transit', () => {
    render(
      <StopsPanel stops={[stop({ status: 'in_transit' })]} onStatus={vi.fn()} onDelete={vi.fn()} />,
    )
    expect(screen.queryByLabelText('Delete Hartford Hospital Lab')).toBeNull()
    expect(screen.getByRole('button', { name: 'Delivered' })).toBeInTheDocument()
  })

  it('marks priority stops', () => {
    render(<StopsPanel stops={[stop({ priority: true })]} onStatus={vi.fn()} onDelete={vi.fn()} />)
    expect(screen.getByText('STAT')).toBeInTheDocument()
  })
})

describe('RoutesPanel', () => {
  it('prompts to optimize when there is no plan', () => {
    render(<RoutesPanel plan={null} stops={[]} focusedRoute={null} onFocus={vi.fn()} />)
    expect(screen.getByText(/No plan yet/)).toBeInTheDocument()
  })

  it('expands the stop sequence when a route is focused', () => {
    const onFocus = vi.fn()
    const { rerender } = render(
      <RoutesPanel plan={plan} stops={[stop()]} focusedRoute={null} onFocus={onFocus} />,
    )
    fireEvent.click(screen.getByRole('button', { pressed: false }))
    expect(onFocus).toHaveBeenCalledWith(1)
    rerender(<RoutesPanel plan={plan} stops={[stop()]} focusedRoute={1} onFocus={onFocus} />)
    expect(screen.getByText('Hartford Hospital Lab')).toBeInTheDocument()
    expect(screen.getByText('30/40 packages')).toBeInTheDocument()
  })
})
