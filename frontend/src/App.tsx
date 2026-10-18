import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import { AddStopForm } from './components/AddStopForm'
import { DriversPanel } from './components/DriversPanel'
import { KpiRow } from './components/KpiRow'
import { MapView } from './components/MapView'
import { RoutesPanel } from './components/RoutesPanel'
import { StopsPanel } from './components/StopsPanel'
import type { Driver, LatLng, NewStop, Plan, Solver, Stop, StopStatus, Summary } from './types'

type Tab = 'routes' | 'stops' | 'drivers'

export default function App() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [drivers, setDrivers] = useState<Driver[]>([])
  const [stops, setStops] = useState<Stop[]>([])
  const [plan, setPlan] = useState<Plan | null>(null)
  const [tab, setTab] = useState<Tab>('routes')
  const [solver, setSolver] = useState<Solver>('ortools')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [focusedRoute, setFocusedRoute] = useState<number | null>(null)
  const [addMode, setAddMode] = useState(false)
  const [draftPoint, setDraftPoint] = useState<LatLng | null>(null)

  const refresh = useCallback(async () => {
    const [s, d, st, p] = await Promise.all([
      api.summary(),
      api.drivers(),
      api.stops(),
      api.latestPlan(),
    ])
    setSummary(s)
    setDrivers(d)
    setStops(st)
    setPlan(p)
  }, [])

  // Wraps an action with busy state, error reporting and a data refresh.
  const run = useCallback(
    async (action: () => Promise<unknown>) => {
      setBusy(true)
      setError(null)
      try {
        await action()
        await refresh()
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Something went wrong')
      } finally {
        setBusy(false)
      }
    },
    [refresh],
  )

  // Initial load. Data is fetched first, so state is only set after the await.
  useEffect(() => {
    const load = async () => {
      try {
        await refresh()
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Could not load data')
      }
    }
    void load()
  }, [refresh])

  const optimize = () =>
    run(async () => {
      await api.optimize(solver)
      setFocusedRoute(null)
      setTab('routes')
    })

  const addStop = (stop: NewStop) =>
    run(async () => {
      await api.createStop(stop)
      setDraftPoint(null)
      setAddMode(false)
    })

  const setStatus = (id: number, status: StopStatus) => run(() => api.setStatus(id, status))
  const deleteStop = (id: number) => run(() => api.deleteStop(id))
  const toggleDriver = (id: number, active: boolean) => run(() => api.toggleDriver(id, active))
  const reset = () =>
    run(async () => {
      await api.resetDemo()
      setFocusedRoute(null)
    })

  const pendingCount = summary?.stops_by_status.pending ?? 0

  return (
    <div className="app">
      <aside className="sidebar">
        <header className="brand">
          <div className="brand-mark" aria-hidden>
            ◆
          </div>
          <div>
            <h1>Courier Dispatch</h1>
            <div className="brand-sub">{summary?.depot.name ?? 'Loading…'}</div>
          </div>
        </header>

        <KpiRow summary={summary} plan={plan} />

        <section className="optimize">
          <div className="segmented" role="radiogroup" aria-label="Solver">
            {(['ortools', 'heuristic'] as Solver[]).map((s) => (
              <button
                type="button"
                key={s}
                role="radio"
                aria-checked={solver === s}
                className={solver === s ? 'on' : ''}
                onClick={() => setSolver(s)}
              >
                {s === 'ortools' ? 'OR-Tools VRP' : '2-opt heuristic'}
              </button>
            ))}
          </div>
          <button type="button" className="btn-primary btn-wide" onClick={optimize} disabled={busy}>
            {busy ? 'Working…' : 'Optimize routes'}
          </button>
          <div className="optimize-hint">
            {pendingCount > 0
              ? `${pendingCount} stop${pendingCount > 1 ? 's' : ''} waiting for a route`
              : 'All open stops are routed'}
          </div>
        </section>

        {error && (
          <div className="error" role="alert">
            {error}
          </div>
        )}

        <nav className="tabs" role="tablist">
          {(['routes', 'stops', 'drivers'] as Tab[]).map((t) => (
            <button
              type="button"
              key={t}
              role="tab"
              aria-selected={tab === t}
              className={tab === t ? 'on' : ''}
              onClick={() => setTab(t)}
            >
              {t[0].toUpperCase() + t.slice(1)}
              <span className="count">
                {t === 'routes' ? (plan?.routes.length ?? 0) : t === 'stops' ? stops.length : drivers.length}
              </span>
            </button>
          ))}
        </nav>

        <div className="panel">
          {tab === 'routes' && (
            <RoutesPanel
              plan={plan}
              stops={stops}
              focusedRoute={focusedRoute}
              onFocus={setFocusedRoute}
            />
          )}
          {tab === 'stops' && (
            <StopsPanel stops={stops} onStatus={setStatus} onDelete={deleteStop} />
          )}
          {tab === 'drivers' && <DriversPanel drivers={drivers} onToggle={toggleDriver} />}
        </div>

        <footer className="sidebar-foot">
          <button type="button" className="link" onClick={reset} disabled={busy}>
            Reset demo data
          </button>
          <a className="link" href="/docs" target="_blank" rel="noreferrer">
            API docs
          </a>
        </footer>
      </aside>

      <main className="map-wrap">
        {summary && (
          <MapView
            depot={summary.depot}
            stops={stops}
            plan={plan}
            focusedRoute={focusedRoute}
            addMode={addMode}
            onMapClick={setDraftPoint}
          />
        )}
        <div className="map-toolbar">
          <button
            type="button"
            className={addMode ? 'btn-secondary on' : 'btn-secondary'}
            onClick={() => {
              setAddMode(!addMode)
              setDraftPoint(null)
            }}
          >
            {addMode ? 'Click the map to place a stop' : '+ Add stop'}
          </button>
        </div>
        <div className="legend">
          <span>
            <i className="dot" style={{ background: '#9aa1a9' }} /> Pending
          </span>
          <span>
            <i className="dot" style={{ background: '#16a34a' }} /> Delivered
          </span>
          <span>
            <i className="dot ring" /> Priority
          </span>
        </div>
        {draftPoint && (
          <AddStopForm
            point={draftPoint}
            onSubmit={addStop}
            onCancel={() => setDraftPoint(null)}
          />
        )}
      </main>
    </div>
  )
}
