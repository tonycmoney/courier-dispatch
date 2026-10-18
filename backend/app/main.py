"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base, SessionLocal, engine, get_db
from app.models import Driver, Stop, StopStatus
from app.routers import dispatch, drivers, stops
from app.schemas import Depot, Summary
from app.seed import seed_if_empty

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    if get_settings().seed_on_startup:
        with SessionLocal() as db:
            seed_if_empty(db)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Courier Dispatch API",
        version="1.0.0",
        description="Dispatch and route optimization for multi stop courier work.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(drivers.router)
    app.include_router(stops.router)
    app.include_router(dispatch.router)

    @app.get("/api/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    @app.get("/api/summary", response_model=Summary, tags=["meta"])
    def summary(db: Session = Depends(get_db)):
        counts = dict(db.execute(select(Stop.status, func.count()).group_by(Stop.status)).all())
        by_status = {s.value: int(counts.get(s, 0)) for s in StopStatus}
        pending_pkgs = db.scalar(
            select(func.coalesce(func.sum(Stop.packages), 0)).where(
                Stop.status == StopStatus.pending
            )
        )
        return Summary(
            depot=Depot(name=settings.depot_name, lat=settings.depot_lat, lng=settings.depot_lng),
            drivers_active=db.scalar(select(func.count()).where(Driver.active.is_(True))),
            stops_total=sum(by_status.values()),
            stops_by_status=by_status,
            packages_pending=int(pending_pkgs),
        )

    # Serve the built React dashboard when it is present (production image).
    if STATIC_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            candidate = STATIC_DIR / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
