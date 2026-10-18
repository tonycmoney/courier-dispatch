"""SQLAlchemy ORM models."""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class StopStatus(str, enum.Enum):
    pending = "pending"
    assigned = "assigned"
    in_transit = "in_transit"
    delivered = "delivered"
    failed = "failed"


# Allowed status transitions. Anything not listed here is rejected by the API.
ALLOWED_TRANSITIONS: dict[StopStatus, set[StopStatus]] = {
    StopStatus.pending: {StopStatus.assigned},
    StopStatus.assigned: {StopStatus.in_transit, StopStatus.pending},
    StopStatus.in_transit: {StopStatus.delivered, StopStatus.failed},
    StopStatus.failed: {StopStatus.pending},
    StopStatus.delivered: set(),
}


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    vehicle: Mapped[str] = mapped_column(String(50), default="cargo_van")
    capacity: Mapped[int] = mapped_column(Integer, default=40)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Stop(Base):
    __tablename__ = "stops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255), default="")
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    packages: Mapped[int] = mapped_column(Integer, default=1)
    priority: Mapped[bool] = mapped_column(Boolean, default=False)
    # Optional delivery window, in minutes after shift start.
    window_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    window_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[StopStatus] = mapped_column(
        Enum(StopStatus, native_enum=False, length=20), default=StopStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Plan(Base):
    """One run of the optimizer: a set of routes, one per driver used."""

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solver: Mapped[str] = mapped_column(String(30))
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    total_duration_min: Mapped[float] = mapped_column(Float, default=0.0)
    unassigned: Mapped[list[int]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    routes: Mapped[list[Route]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="Route.id"
    )


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id", ondelete="CASCADE"))
    stop_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    duration_min: Mapped[float] = mapped_column(Float, default=0.0)
    load: Mapped[int] = mapped_column(Integer, default=0)

    plan: Mapped[Plan] = relationship(back_populates="routes")
    driver: Mapped[Driver] = relationship()
