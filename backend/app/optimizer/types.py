"""Plain data types shared by the solvers. No database or web dependencies."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Location:
    lat: float
    lng: float


@dataclass(frozen=True)
class Job:
    id: int
    location: Location
    demand: int = 1
    priority: bool = False
    window: tuple[int, int] | None = None  # minutes after shift start


@dataclass(frozen=True)
class Vehicle:
    id: int
    capacity: int


@dataclass(frozen=True)
class Problem:
    depot: Location
    vehicles: list[Vehicle]
    jobs: list[Job]
    speed_kmh: float = 50.0
    road_factor: float = 1.3
    service_minutes: int = 5
    shift_minutes: int = 600


@dataclass
class VehicleRoute:
    vehicle_id: int
    job_ids: list[int]
    distance_km: float
    duration_min: float
    load: int


@dataclass
class Solution:
    solver: str
    routes: list[VehicleRoute]
    unassigned: list[int] = field(default_factory=list)

    @property
    def total_distance_km(self) -> float:
        return round(sum(r.distance_km for r in self.routes), 2)

    @property
    def total_duration_min(self) -> float:
        return round(sum(r.duration_min for r in self.routes), 1)
