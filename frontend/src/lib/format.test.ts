import { describe, expect, it } from 'vitest'
import {
  formatKm,
  formatMinutes,
  formatWindow,
  NEXT_STATUS,
  ROUTE_COLORS,
  routeColor,
  utilization,
} from './format'

describe('formatMinutes', () => {
  it('formats minutes only', () => expect(formatMinutes(42)).toBe('42m'))
  it('formats whole hours', () => expect(formatMinutes(120)).toBe('2h'))
  it('formats hours and minutes', () => expect(formatMinutes(409.7)).toBe('6h 50m'))
})

describe('formatKm', () => {
  it('keeps one decimal under 100 km', () => expect(formatKm(42.345)).toBe('42.3 km'))
  it('rounds at 100 km and over', () => expect(formatKm(266.34)).toBe('266 km'))
})

describe('formatWindow', () => {
  it('returns empty when no window', () => expect(formatWindow(null, null)).toBe(''))
  it('converts offsets from an 8am shift start', () => {
    expect(formatWindow(0, 180)).toBe('8:00am to 11:00am')
    expect(formatWindow(270, 300)).toBe('12:30pm to 1:00pm')
  })
})

describe('routeColor', () => {
  it('cycles through the palette', () => {
    expect(routeColor(0)).toBe(ROUTE_COLORS[0])
    expect(routeColor(ROUTE_COLORS.length)).toBe(ROUTE_COLORS[0])
  })
})

describe('utilization', () => {
  it('computes a percentage', () => expect(utilization(30, 40)).toBe(75))
  it('caps at 100', () => expect(utilization(50, 40)).toBe(100))
  it('handles zero capacity', () => expect(utilization(5, 0)).toBe(0))
})

describe('NEXT_STATUS', () => {
  it('treats delivered as final', () => expect(NEXT_STATUS.delivered).toEqual([]))
  it('lets a failed stop be retried', () => expect(NEXT_STATUS.failed).toEqual(['pending']))
})
