import { formatWindow, NEXT_STATUS, STATUS_LABEL } from '../lib/format'
import type { Stop, StopStatus } from '../types'

interface Props {
  stops: Stop[]
  onStatus: (id: number, status: StopStatus) => void
  onDelete: (id: number) => void
}

export function StopsPanel({ stops, onStatus, onDelete }: Props) {
  if (stops.length === 0) return <p className="empty">No stops yet.</p>
  return (
    <ul className="stop-list">
      {stops.map((stop) => (
        <li key={stop.id} className="stop-row">
          <div className="stop-main">
            <div className="stop-title">
              {stop.priority && <span className="badge-priority">STAT</span>}
              {stop.label}
            </div>
            <div className="stop-sub">
              {stop.packages} pkg
              {stop.window_start !== null &&
                ` · ${formatWindow(stop.window_start, stop.window_end)}`}
            </div>
          </div>
          <div className="stop-actions">
            <span className={`status status-${stop.status}`}>{STATUS_LABEL[stop.status]}</span>
            {NEXT_STATUS[stop.status].map((next) => (
              <button
                type="button"
                key={next}
                className="chip"
                onClick={() => onStatus(stop.id, next)}
              >
                {next === 'in_transit' ? 'Start' : next === 'pending' ? 'Retry' : STATUS_LABEL[next]}
              </button>
            ))}
            {stop.status !== 'in_transit' && (
              <button
                type="button"
                className="chip chip-ghost"
                aria-label={`Delete ${stop.label}`}
                onClick={() => onDelete(stop.id)}
              >
                ✕
              </button>
            )}
          </div>
        </li>
      ))}
    </ul>
  )
}
