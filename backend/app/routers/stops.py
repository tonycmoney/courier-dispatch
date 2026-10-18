from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ALLOWED_TRANSITIONS, Stop, StopStatus
from app.schemas import StatusUpdate, StopCreate, StopOut

router = APIRouter(prefix="/api/stops", tags=["stops"])


def _get_or_404(db: Session, stop_id: int) -> Stop:
    stop = db.get(Stop, stop_id)
    if stop is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Stop not found")
    return stop


@router.get("", response_model=list[StopOut])
def list_stops(
    status_filter: StopStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    query = select(Stop).order_by(Stop.id)
    if status_filter is not None:
        query = query.where(Stop.status == status_filter)
    return db.scalars(query).all()


@router.post("", response_model=StopOut, status_code=status.HTTP_201_CREATED)
def create_stop(payload: StopCreate, db: Session = Depends(get_db)):
    stop = Stop(**payload.model_dump())
    db.add(stop)
    db.commit()
    db.refresh(stop)
    return stop


@router.patch("/{stop_id}/status", response_model=StopOut)
def update_status(stop_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    stop = _get_or_404(db, stop_id)
    if payload.status == stop.status:
        return stop
    if payload.status not in ALLOWED_TRANSITIONS[stop.status]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot move stop from {stop.status.value} to {payload.status.value}",
        )
    stop.status = payload.status
    db.commit()
    db.refresh(stop)
    return stop


@router.delete("/{stop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stop(stop_id: int, db: Session = Depends(get_db)):
    stop = _get_or_404(db, stop_id)
    if stop.status == StopStatus.in_transit:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cannot delete a stop that is in transit")
    db.delete(stop)
    db.commit()
