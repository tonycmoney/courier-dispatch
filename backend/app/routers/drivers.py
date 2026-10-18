from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Driver
from app.schemas import DriverCreate, DriverOut, DriverUpdate

router = APIRouter(prefix="/api/drivers", tags=["drivers"])


def _get_or_404(db: Session, driver_id: int) -> Driver:
    driver = db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Driver not found")
    return driver


@router.get("", response_model=list[DriverOut])
def list_drivers(db: Session = Depends(get_db)):
    return db.scalars(select(Driver).order_by(Driver.id)).all()


@router.post("", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
def create_driver(payload: DriverCreate, db: Session = Depends(get_db)):
    driver = Driver(**payload.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.patch("/{driver_id}", response_model=DriverOut)
def update_driver(driver_id: int, payload: DriverUpdate, db: Session = Depends(get_db)):
    driver = _get_or_404(db, driver_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)
    db.commit()
    db.refresh(driver)
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, driver_id))
    db.commit()
