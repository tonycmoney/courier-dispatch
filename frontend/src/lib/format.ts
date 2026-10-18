import type { StopStatus } from '../types'

export const ROUTE_COLORS = ['#2563eb', '#ff5a1f', '#0d9488', '#9333ea', '#ca8a04', '#db2777']

export function routeColor(index: number): string {
  return ROUTE_COLORS[((index % ROUTE_COLORS.length) + ROUTE_COLORS.length) % ROUTE_COLORS.length]
}

export function formatMinutes(total: number): string {
  const mins = Math.round(total)
  const h = Math.floor(mins / 60)
  const m = mins % 60
  if (h === 0) return `${m}m`
  return m === 0 ? `${h}h` : `${h}h ${m}m`
}

export function formatKm(km: number): string {
  return km >= 100 ? `${Math.round(km)} km` : `${km.toFixed(1)} km`
}

/** Window values are minutes after shift start (8:00 AM). */
export function formatWindow(start: number | null, end: number | null, shiftStartHour = 8): string {
  if (start === null || end === null) return ''
  const clock = (m: number) => {
    const total = shiftStartHour * 60 + m
    const h24 = Math.floor(total / 60) % 24
    const mm = String(total % 60).padStart(2, '0')
    const suffix = h24 >= 12 ? 'pm' : 'am'
    const h12 = h24 % 12 === 0 ? 12 : h24 % 12
    return `${h12}:${mm}${suffix}`
  }
  return `${clock(start)} to ${clock(end)}`
}

export const STATUS_LABEL: Record<StopStatus, string> = {
  pending: 'Pending',
  assigned: 'Assigned',
  in_transit: 'In transit',
  delivered: 'Delivered',
  failed: 'Failed',
}

/** Next statuses a dispatcher can move a stop to. Mirrors the API state machine. */
export const NEXT_STATUS: Record<StopStatus, StopStatus[]> = {
  pending: [],
  assigned: ['in_transit'],
  in_transit: ['delivered', 'failed'],
  failed: ['pending'],
  delivered: [],
}

export function utilization(load: number, capacity: number): number {
  if (capacity <= 0) return 0
  return Math.min(100, Math.round((load / capacity) * 100))
}
