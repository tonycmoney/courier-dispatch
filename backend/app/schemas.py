"""Pydantic request and response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import StopStatus


class DriverBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    vehicle: Literal["cargo_van", "minivan", "box_truck", "car"] = "cargo_van"
    capacity: int = Field(default=40, ge=1, le=1000)
    active: bool = True


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    vehicle: Literal["cargo_van", "minivan", "box_truck", "car"] | None = None
    capacity: int | None = Field(default=None, ge=1, le=1000)
    active: bool | None = None


class DriverOut(DriverBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class StopBase(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    address: str = Field(default="", max_length=255)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    packages: int = Field(default=1, ge=1, le=500)
    priority: bool = False
    window_start: int | None = Field(default=None, ge=0, le=1440)
    window_end: int | None = Field(default=None, ge=0, le=1440)

    @model_validator(mode="after")
    def check_window(self):
        if (self.window_start is None) != (self.window_end is None):
            raise ValueError("window_start and window_end must be set together")
        if self.window_start is not None and self.window_end <= self.window_start:
            raise ValueError("window_end must be after window_start")
        return self


class StopCreate(StopBase):
    pass


class StopOut(StopBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: StopStatus
    created_at: datetime


class StatusUpdate(BaseModel):
    status: StopStatus


class OptimizeRequest(BaseModel):
    solver: Literal["ortools", "heuristic"] = "ortools"
    time_limit_s: int | None = Field(default=None, ge=1, le=30)


class LatLng(BaseModel):
    lat: float
    lng: float


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    driver_id: int
    driver_name: str
    stop_ids: list[int]
    distance_km: float
    duration_min: float
    load: int
    capacity: int
    path: list[LatLng]


class PlanOut(BaseModel):
    id: int
    solver: str
    total_distance_km: float
    total_duration_min: float
    unassigned: list[int]
    created_at: datetime
    routes: list[RouteOut]


class Depot(BaseModel):
    name: str
    lat: float
    lng: float


class Summary(BaseModel):
    depot: Depot
    drivers_active: int
    stops_total: int
    stops_by_status: dict[str, int]
    packages_pending: int
