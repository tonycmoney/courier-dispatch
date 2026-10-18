"""Application settings, read from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./dispatch.db"

    # Depot (where every route starts and ends). Defaults to Cheshire, CT.
    depot_name: str = "Cheshire Depot"
    depot_lat: float = 41.4990
    depot_lng: float = -72.9007

    # Routing assumptions
    avg_speed_kmh: float = 50.0
    road_factor: float = 1.3  # straight line distance -> estimated road distance
    service_minutes: int = 5  # time spent at each stop
    shift_minutes: int = 600  # 10 hour shift
    solver_time_limit_s: int = 3

    # Seed demo data on startup when the database is empty
    seed_on_startup: bool = True
    allow_demo_reset: bool = True

    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()
