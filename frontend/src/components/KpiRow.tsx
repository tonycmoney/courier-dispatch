import { formatKm, formatMinutes } from '../lib/format'
import type { Plan, Summary } from '../types'

interface Props {
  summary: Summary | null
  plan: Plan | null
}

export function KpiRow({ summary, plan }: Props) {
  const delivered = summary?.stops_by_status.delivered ?? 0
  const total = summary?.stops_total ?? 0
  const items = [
    { label: 'Stops', value: total ? `${delivered}/${total}` : '0', hint: 'delivered' },
    { label: 'Pending pkgs', value: String(summary?.packages_pending ?? 0), hint: 'not routed' },
    { label: 'Drivers', value: String(summary?.drivers_active ?? 0), hint: 'active' },
    {
      label: 'Plan',
      value: plan ? formatKm(plan.total_distance_km) : '—',
      hint: plan ? formatMinutes(plan.total_duration_min) + ' drive' : 'not optimized',
    },
  ]
  return (
    <div className="kpis" role="list">
      {items.map((k) => (
        <div className="kpi" role="listitem" key={k.label}>
          <div className="kpi-label">{k.label}</div>
          <div className="kpi-value">{k.value}</div>
          <div className="kpi-hint">{k.hint}</div>
        </div>
      ))}
    </div>
  )
}
