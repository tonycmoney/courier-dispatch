# Courier Dispatch

[![CI](https://github.com/tonycmoney/courier-dispatch/actions/workflows/ci.yml/badge.svg)](https://github.com/tonycmoney/courier-dispatch/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![React](https://img.shields.io/badge/react-19-61dafb)
![License](https://img.shields.io/badge/license-MIT-green)

Dispatch and route optimization for multi stop courier work. Add stops, put drivers on shift, and get optimized routes that respect van capacity, shift length, priority (STAT) deliveries and delivery time windows.

**Live demo:** https://web-production-33a98.up.railway.app
**API docs:** https://web-production-33a98.up.railway.app/docs

The demo is seeded with 18 medical and business stops across central Connecticut and three drivers working out of a Cheshire depot. Use **Reset demo data** in the sidebar to start over.

![Optimized routes on the dispatch dashboard](docs/screenshots/2-optimized.png)

## Why I built it

I've spent over 15 years in delivery and dispatch, including medical courier routes where a lab pickup has a hard window and a missed stop is not an option. Most small courier operations still plan routes by hand or with a consumer map app. This project is the tool I wanted: a real vehicle routing solver behind a dashboard a dispatcher can actually use.

## Features

* **Two route solvers behind one interface**
  * **OR-Tools VRP:** capacitated vehicle routing with time windows, shift limits and drop penalties, solved with guided local search
  * **Nearest neighbor + 2-opt:** a fast, dependency free baseline to compare against
* **Priority aware:** when there isn't enough capacity, normal stops are dropped before priority ones, and the plan reports what couldn't be routed
* **Delivery lifecycle:** stops move through `pending → assigned → in_transit → delivered / failed`, enforced by a state machine in the API (invalid moves return `409`)
* **Re-planning:** optimize again mid day and only stops that haven't left the depot are re-planned
* **Dashboard:** color coded routes on a map, load meters per van, stop sequences, click the map to add a stop, toggle drivers on and off shift
* **Postgres in production, SQLite locally**, with zero code changes

## Results on the demo data

| Solver | Total distance | Total drive + service time | Vans used |
|---|---|---|---|
| Nearest neighbor + 2-opt | 309 km | 7h 41m | 2 |
| **OR-Tools VRP** | **266 km** | **6h 50m** | 2 |

The OR-Tools plan is about **14% shorter** and also honors every delivery window. A test in CI checks that the VRP solver never does worse than the baseline.

## Architecture

```mermaid
flowchart LR
    subgraph Browser
        UI["React + TypeScript dashboard<br/>Leaflet map"]
    end

    subgraph Container["Docker container (Railway)"]
        API["FastAPI<br/>REST API + static files"]
        subgraph Optimizer["optimizer package"]
            VRP["OR-Tools VRP<br/>capacity, windows, shifts"]
            H["Nearest neighbor + 2-opt"]
            D["Haversine distance<br/>matrix"]
        end
        ORM["SQLAlchemy models<br/>drivers, stops, plans, routes"]
    end

    DB[("PostgreSQL")]

    UI -- "JSON over HTTPS" --> API
    API --> Optimizer
    VRP --> D
    H --> D
    API --> ORM --> DB
```

**Request flow for "Optimize routes":**

1. The API loads active drivers and every stop that is `pending` or `assigned` (stops already in transit are left alone).
2. It converts them into plain dataclasses (`Problem`, `Vehicle`, `Job`). The optimizer has no database or web dependencies, which keeps it fast to test.
3. The chosen solver builds a distance matrix (haversine distance × road factor) and returns routes plus any unassigned stops.
4. The API saves a `Plan` with one `Route` per van, updates stop statuses, and returns map ready paths to the dashboard.

### Project layout

```
backend/
  app/
    main.py            FastAPI app, summary endpoint, serves the built dashboard
    models.py          ORM models and the stop status state machine
    schemas.py         Pydantic request/response validation
    routers/           drivers, stops, dispatch endpoints
    optimizer/         solvers, distance math, shared types
  tests/               pytest: optimizer correctness + API behavior
frontend/
  src/
    components/        Map, route cards, stops, drivers, add stop form
    lib/format.ts      formatting and status rules (unit tested)
    api.ts             typed API client
Dockerfile             multi stage: build React, then run FastAPI as non root
.github/workflows/     CI and screenshot automation
```

## Running locally

**Requirements:** Python 3.11+ and Node 20+.

```bash
git clone https://github.com/tonycmoney/courier-dispatch.git
cd courier-dispatch

# Backend (http://localhost:8000)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

# Frontend, in a second terminal (http://localhost:5173, proxies /api to :8000)
cd frontend
npm install
npm run dev
```

The backend uses SQLite by default and seeds demo data on first start. Settings such as depot location, average speed and shift length are environment variables; see [`.env.example`](.env.example).

### With Docker

```bash
docker build -t courier-dispatch .
docker run -p 8000:8000 courier-dispatch
# open http://localhost:8000
```

To use Postgres, pass `-e DATABASE_URL=postgresql://user:pass@host:5432/dbname`, or the separate `DB_HOST`, `DB_USER`, `DB_PASSWORD` and `DB_NAME` variables.

### Production on AWS

The demo runs on Railway for simplicity. A hardened AWS deployment of this same image (ECS Fargate in private subnets, WAF, KMS encrypted RDS, credentials from Secrets Manager, CloudTrail, GuardDuty) is defined in Terraform in [secure-cloud-infrastructure](https://github.com/tonycmoney/secure-cloud-infrastructure).

## Testing

```bash
cd backend && pytest --cov=app        # 31 tests, 96% coverage
cd frontend && npm test               # 20 tests
```

Highlights from the test suite:

* Both solvers serve every stop exactly once and never exceed van capacity or shift length
* With one small van, the solver drops stops but keeps every priority stop
* Arrival times recomputed along OR-Tools routes fall inside each delivery window
* The status state machine rejects skipping steps and treats `delivered` as final
* Re-optimizing leaves in transit stops alone and ignores off shift drivers

**CI** runs on every push: ruff lint and format check, pytest on SQLite, a smoke test against a real Postgres service, frontend lint, typecheck, tests and build, then builds the Docker image, boots it and runs an optimization inside the container.

## API overview

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/summary` | Depot, counts by status, pending packages |
| `GET` `POST` | `/api/drivers` | List or add drivers |
| `PATCH` `DELETE` | `/api/drivers/{id}` | Update (e.g. take off shift) or remove |
| `GET` `POST` | `/api/stops` | List (filter with `?status=`) or add stops |
| `PATCH` | `/api/stops/{id}/status` | Move a stop through its lifecycle |
| `POST` | `/api/dispatch/optimize` | Plan routes (`{"solver": "ortools" \| "heuristic"}`) |
| `GET` | `/api/dispatch/plans/latest` | Most recent plan with map paths |

Full interactive docs are at [`/docs`](https://web-production-33a98.up.railway.app/docs).

## More screenshots

| Route detail | Stop lifecycle |
|---|---|
| ![Route detail](docs/screenshots/3-route-detail.png) | ![Stops](docs/screenshots/4-stops.png) |

| Mobile | API docs |
|---|---|
| ![Mobile](docs/screenshots/5-mobile.png) | ![API docs](docs/screenshots/6-api-docs.png) |

Screenshots are captured from the live site by the [Update screenshots](.github/workflows/screenshots.yml) workflow.

## Design decisions and tradeoffs

* **Straight line distance × road factor instead of a routing engine.** It keeps the app free to run and fully testable offline. Swapping in OSRM or a maps API only means replacing `distance_matrix_km`.
* **Every stop is optional to the solver, with a penalty for dropping it.** A real dispatcher needs the best possible plan for a bad day, not an error. Priority stops carry a penalty 100× larger.
* **The optimizer works on plain dataclasses.** No ORM objects cross that boundary, so solver tests run in milliseconds and the solver could move to a background worker unchanged.
* **One container serves both the API and the built dashboard.** Simple to deploy and no CORS setup in production.

## Possible next steps

* Real road distances and traffic aware travel times
* Driver mobile view with proof of delivery photos
* Background job queue for large problems (hundreds of stops)
* Authentication and per company data

## License

MIT
