import type { Driver } from '../types'

const VEHICLE_LABEL: Record<Driver['vehicle'], string> = {
  cargo_van: 'Cargo van',
  minivan: 'Minivan',
  box_truck: 'Box truck',
  car: 'Car',
}

interface Props {
  drivers: Driver[]
  onToggle: (id: number, active: boolean) => void
}

export function DriversPanel({ drivers, onToggle }: Props) {
  return (
    <ul className="driver-list">
      {drivers.map((d) => (
        <li key={d.id} className={d.active ? 'driver-row' : 'driver-row off'}>
          <div>
            <div className="stop-title">{d.name}</div>
            <div className="stop-sub">
              {VEHICLE_LABEL[d.vehicle]} · {d.capacity} pkg capacity
            </div>
          </div>
          <label className="switch">
            <input
              type="checkbox"
              checked={d.active}
              onChange={(e) => onToggle(d.id, e.target.checked)}
              aria-label={`${d.name} on shift`}
            />
            <span>{d.active ? 'On shift' : 'Off'}</span>
          </label>
        </li>
      ))}
    </ul>
  )
}
