export type StopStatus = 'pending' | 'assigned' | 'in_transit' | 'delivered' | 'failed'
export type Vehicle = 'cargo_van' | 'minivan' | 'box_truck' | 'car'
export type Solver = 'ortools' | 'heuristic'

export interface Driver {
  id: number
  name: string
  vehicle: Vehicle
  capacity: number
  active: boolean
}

export interface Stop {
  id: number
  label: string
  address: string
  lat: number
  lng: number
  packages: number
  priority: boolean
  window_start: number | null
  window_end: number | null
  status: StopStatus
}

export interface NewStop {
  label: string
  address: string
  lat: number
  lng: number
  packages: number
  priority: boolean
}

export interface LatLng {
  lat: number
  lng: number
}

export interface Route {
  id: number
  driver_id: number
  driver_name: string
  stop_ids: number[]
  distance_km: number
  duration_min: number
  load: number
  capacity: number
  path: LatLng[]
}

export interface Plan {
  id: number
  solver: Solver
  total_distance_km: number
  total_duration_min: number
  unassigned: number[]
  created_at: string
  routes: Route[]
}

export interface Summary {
  depot: { name: string; lat: number; lng: number }
  drivers_active: number
  stops_total: number
  stops_by_status: Record<StopStatus, number>
  packages_pending: number
}
