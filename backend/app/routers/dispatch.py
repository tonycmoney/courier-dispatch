from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import optimizer
from app.config import Settings, get_settings
from app.db import get_db
from app.models import Driver, Plan, Route, Stop, StopStatus
from app.schemas import LatLng, OptimizeRequest, PlanOut, RouteOut
from app.seed import reset

router = APIRouter(prefix="/api", tags=["dispatch"])

# Stops the optimizer may (re)plan. In transit and finished stops are left alone.
PLANNABLE = (StopStatus.pending, StopStatus.assigned)


def build_problem(
    settings: Settings, drivers: list[Driver], stops: list[Stop]
) -> optimizer.Problem:
    return optimizer.Problem(
        depot=optimizer.Location(settings.depot_lat, settings.depot_lng),
        vehicles=[optimizer.Vehicle(id=d.id, capacity=d.capacity) for d in drivers],
        jobs=[
            optimizer.Job(
                id=s.id,
                location=optimizer.Location(s.lat, s.lng),
                demand=s.packages,
                priority=s.priority,
                window=(s.window_start, s.window_end) if s.window_start is not None else None,
            )
            for s in stops
        ],
        speed_kmh=settings.avg_speed_kmh,
        road_factor=settings.road_factor,
        service_minutes=settings.service_minutes,
        shift_minutes=settings.shift_minutes,
    )


def plan_to_schema(plan: Plan, db: Session, settings: Settings) -> PlanOut:
    stop_ids = {sid for r in plan.routes for sid in r.stop_ids}
    stops = {s.id: s for s in db.scalars(select(Stop).where(Stop.id.in_(stop_ids)))}
    depot = LatLng(lat=settings.depot_lat, lng=settings.depot_lng)
    routes = []
    for r in plan.routes:
        path = [depot]
        path += [LatLng(lat=stops[i].lat, lng=stops[i].lng) for i in r.stop_ids if i in stops]
        path.append(depot)
        routes.append(
            RouteOut(
                id=r.id,
                driver_id=r.driver_id,
                driver_name=r.driver.name,
                stop_ids=r.stop_ids,
                distance_km=r.distance_km,
                duration_min=r.duration_min,
                load=r.load,
                capacity=r.driver.capacity,
                path=path,
            )
        )
    return PlanOut(
        id=plan.id,
        solver=plan.solver,
        total_distance_km=plan.total_distance_km,
        total_duration_min=plan.total_duration_min,
        unassigned=plan.unassigned,
        created_at=plan.created_at,
        routes=routes,
    )


@router.post("/dispatch/optimize", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def optimize(
    payload: OptimizeRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    drivers = list(db.scalars(select(Driver).where(Driver.active.is_(True)).order_by(Driver.id)))
    stops = list(db.scalars(select(Stop).where(Stop.status.in_(PLANNABLE)).order_by(Stop.id)))
    if not drivers:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No active drivers")
    if not stops:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No stops to plan")

    problem = build_problem(settings, drivers, stops)
    solution = optimizer.solve(
        problem,
        solver=payload.solver,
        time_limit_s=payload.time_limit_s or settings.solver_time_limit_s,
    )

    plan = Plan(
        solver=solution.solver,
        total_distance_km=solution.total_distance_km,
        total_duration_min=solution.total_duration_min,
        unassigned=solution.unassigned,
    )
    for r in solution.routes:
        plan.routes.append(
            Route(
                driver_id=r.vehicle_id,
                stop_ids=r.job_ids,
                distance_km=r.distance_km,
                duration_min=r.duration_min,
                load=r.load,
            )
        )
    db.add(plan)

    assigned = {sid for r in solution.routes for sid in r.job_ids}
    for stop in stops:
        stop.status = StopStatus.assigned if stop.id in assigned else StopStatus.pending

    db.commit()
    db.refresh(plan)
    return plan_to_schema(plan, db, settings)


@router.get("/dispatch/plans/latest", response_model=PlanOut | None)
def latest_plan(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    plan = db.scalars(
        select(Plan)
        .options(selectinload(Plan.routes).selectinload(Route.driver))
        .order_by(Plan.id.desc())
        .limit(1)
    ).first()
    return plan_to_schema(plan, db, settings) if plan else None


@router.post("/demo/reset", status_code=status.HTTP_204_NO_CONTENT)
def demo_reset(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    if not settings.allow_demo_reset:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Demo reset is disabled")
    reset(db)
