import { useState } from 'react'
import type { LatLng, NewStop } from '../types'

interface Props {
  point: LatLng
  onSubmit: (stop: NewStop) => void
  onCancel: () => void
}

export function AddStopForm({ point, onSubmit, onCancel }: Props) {
  const [label, setLabel] = useState('')
  const [packages, setPackages] = useState(1)
  const [priority, setPriority] = useState(false)

  return (
    <form
      className="add-form"
      onSubmit={(e) => {
        e.preventDefault()
        if (!label.trim()) return
        onSubmit({ label: label.trim(), address: '', packages, priority, ...point })
      }}
    >
      <div className="add-form-title">New stop</div>
      <div className="add-form-coords">
        {point.lat.toFixed(4)}, {point.lng.toFixed(4)}
      </div>
      <label>
        Name
        <input
          autoFocus
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="e.g. Meriden Lab"
          maxLength={120}
          required
        />
      </label>
      <label>
        Packages
        <input
          type="number"
          min={1}
          max={500}
          value={packages}
          onChange={(e) => setPackages(Number(e.target.value))}
        />
      </label>
      <label className="check">
        <input type="checkbox" checked={priority} onChange={(e) => setPriority(e.target.checked)} />
        Priority (STAT)
      </label>
      <div className="add-form-actions">
        <button type="button" className="btn-secondary" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn-primary">
          Add stop
        </button>
      </div>
    </form>
  )
}
