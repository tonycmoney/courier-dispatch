import L from 'leaflet'
import { useEffect, useMemo } from 'react'
import {
  CircleMarker,
  MapContainer,
  Marker,
  Polyline,
  TileLayer,
  Tooltip,
  useMap,
  useMapEvents,
} from 'react-leaflet'
import { routeColor, STATUS_LABEL } from '../lib/format'
import type { LatLng, Plan, Stop } from '../types'

interface Props {
  depot: LatLng & { name: string }
  stops: Stop[]
  plan: Plan | null
  focusedRoute: number | null
  addMode: boolean
  onMapClick: (point: LatLng) => void
}

const depotIcon = L.divIcon({
  className: 'depot-icon',
  html: '<div class="depot-pin"><span>D</span></div>',
  iconSize: [30, 30],
  iconAnchor: [15, 15],
})

function FitToStops({ points }: { points: LatLng[] }) {
  const map = useMap()
  const key = points.length
  useEffect(() => {
    if (points.length < 2) return
    map.fitBounds(L.latLngBounds(points.map((p) => [p.lat, p.lng])), { padding: [40, 40] })
    // Only refit when the number of points changes, not on every status update.
  }, [key, map]) // eslint-disable-line react-hooks/exhaustive-deps
  return null
}

function ClickHandler({ enabled, onClick }: { enabled: boolean; onClick: (p: LatLng) => void }) {
  useMapEvents({
    click(e) {
      if (enabled) onClick({ lat: e.latlng.lat, lng: e.latlng.lng })
    },
  })
  return null
}

export function MapView({ depot, stops, plan, focusedRoute, addMode, onMapClick }: Props) {
  // Map each stop to the index of the route that serves it.
  const routeIndexByStop = useMemo(() => {
    const out = new Map<number, number>()
    plan?.routes.forEach((r, i) => r.stop_ids.forEach((id) => out.set(id, i)))
    return out
  }, [plan])

  const sequenceByStop = useMemo(() => {
    const out = new Map<number, number>()
    plan?.routes.forEach((r) => r.stop_ids.forEach((id, i) => out.set(id, i + 1)))
    return out
  }, [plan])

  const allPoints = useMemo(() => [depot, ...stops], [depot, stops])

  return (
    <MapContainer
      center={[depot.lat, depot.lng]}
      zoom={10}
      className={addMode ? 'map map-add-mode' : 'map'}
      zoomControl={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        maxZoom={19}
      />
      <FitToStops points={allPoints} />
      <ClickHandler enabled={addMode} onClick={onMapClick} />

      {plan?.routes.map((route, i) => {
        const dimmed = focusedRoute !== null && focusedRoute !== route.id
        return (
          <Polyline
            key={route.id}
            positions={route.path.map((p) => [p.lat, p.lng])}
            pathOptions={{
              color: routeColor(i),
              weight: focusedRoute === route.id ? 5 : 3.5,
              opacity: dimmed ? 0.15 : 0.85,
              dashArray: route.path.length > 2 ? undefined : '4 6',
            }}
          />
        )
      })}

      {stops.map((stop) => {
        const routeIdx = routeIndexByStop.get(stop.id)
        const onRoute = routeIdx !== undefined && stop.status !== 'pending'
        const route = onRoute ? plan?.routes[routeIdx] : undefined
        const dimmed = focusedRoute !== null && route?.id !== focusedRoute
        let fill = '#9aa1a9'
        if (stop.status === 'delivered') fill = '#16a34a'
        else if (stop.status === 'failed') fill = '#dc2626'
        else if (onRoute) fill = routeColor(routeIdx)
        return (
          <CircleMarker
            key={stop.id}
            center={[stop.lat, stop.lng]}
            radius={stop.priority ? 9 : 7}
            pathOptions={{
              color: stop.priority ? '#16191d' : '#ffffff',
              weight: stop.priority ? 2.5 : 2,
              fillColor: fill,
              fillOpacity: dimmed ? 0.25 : 1,
              opacity: dimmed ? 0.3 : 1,
            }}
          >
            <Tooltip direction="top" offset={[0, -6]}>
              <strong>
                {onRoute && sequenceByStop.get(stop.id) ? `#${sequenceByStop.get(stop.id)} ` : ''}
                {stop.label}
              </strong>
              <br />
              {stop.packages} pkg · {STATUS_LABEL[stop.status]}
              {stop.priority ? ' · Priority' : ''}
            </Tooltip>
          </CircleMarker>
        )
      })}

      <Marker position={[depot.lat, depot.lng]} icon={depotIcon}>
        <Tooltip direction="top" offset={[0, -14]}>
          {depot.name}
        </Tooltip>
      </Marker>
    </MapContainer>
  )
}
