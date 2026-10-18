import type { Driver, NewStop, Plan, Solver, Stop, StopStatus, Summary } from './types'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      // Body was not JSON; keep the status text.
    }
    throw new ApiError(res.status, detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  summary: () => request<Summary>('/api/summary'),
  drivers: () => request<Driver[]>('/api/drivers'),
  stops: () => request<Stop[]>('/api/stops'),
  latestPlan: () => request<Plan | null>('/api/dispatch/plans/latest'),

  optimize: (solver: Solver) =>
    request<Plan>('/api/dispatch/optimize', {
      method: 'POST',
      body: JSON.stringify({ solver }),
    }),

  createStop: (stop: NewStop) =>
    request<Stop>('/api/stops', { method: 'POST', body: JSON.stringify(stop) }),

  setStatus: (id: number, status: StopStatus) =>
    request<Stop>(`/api/stops/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  deleteStop: (id: number) => request<void>(`/api/stops/${id}`, { method: 'DELETE' }),

  toggleDriver: (id: number, active: boolean) =>
    request<Driver>(`/api/drivers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ active }),
    }),

  resetDemo: () => request<void>('/api/demo/reset', { method: 'POST' }),
}
