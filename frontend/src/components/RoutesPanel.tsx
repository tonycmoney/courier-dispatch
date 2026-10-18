import { formatKm, formatMinutes, routeColor, utilization } from '../lib/format'
import type { Plan, Stop } from '../types'

interface Props {
  plan: Plan | null
  stops: Stop[]
  focusedRoute: number | null
  onFocus: (routeId: number | null) => void
}

export function RoutesPanel({ plan, stops, focusedRoute, onFocus }: Props) {
  if (!plan) {
    return (
      <p className="empty">
        No plan yet. Press <strong>Optimize routes</strong> to assign stops to drivers.
      </p>
    )
  }
  const byId = new Map(stops.map((s) => [s.id, s]))
  return (
    <div className="routes">
      <div className="plan-meta">
        Plan #{plan.id} · {plan.solver === 'ortools' ? 'OR-Tools VRP' : 'Heuristic'} ·{' '}
        {new Date(plan.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
      </div>
      {plan.unassigned.length > 0 && (
        <div className="warning">
          {plan.unassigned.length} stop{plan.unassigned.length > 1 ? 's' : ''} could not fit in
          any route (capacity, shift or delivery window).
        </div>
      )}
      {plan.routes.map((route, i) => {
        const pct = utilization(route.load, route.capacity)
        const active = focusedRoute === route.id
        return (
          <button
            type="button"
            key={route.id}
            className={active ? 'route-card active' : 'route-card'}
            onClick={() => onFocus(active ? null : route.id)}
            aria-pressed={active}
          >
            <div className="route-head">
              <span className="swatch" style={{ background: routeColor(i) }} />
              <span className="route-driver">{route.driver_name}</span>
              <span className="route-stats">
                {route.stop_ids.length} stops · {formatKm(route.distance_km)} ·{' '}
                {formatMinutes(route.duration_min)}
              </span>
            </div>
            <div className="meter" aria-label={`Load ${pct}%`}>
              <div style={{ width: `${pct}%`, background: routeColor(i) }} />
            </div>
            <div className="meter-caption">
              {route.load}/{route.capacity} packages
            </div>
            {active && (
              <ol className="sequence">
                {route.stop_ids.map((id) => (
                  <li key={id}>{byId.get(id)?.label ?? `Stop ${id}`}</li>
                ))}
              </ol>
            )}
          </button>
        )
      })}
    </div>
  )
}
