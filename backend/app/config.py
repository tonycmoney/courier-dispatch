"""Application settings, read from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./dispatch.db"

    # Alternative to DATABASE_URL: separate parts, as injected by AWS Secrets
    # Manager (see github.com/tonycmoney/secure-cloud-infrastructure).
    db_host: str | None = None
    db_port: int = 5432
    db_name: str = "app"
    db_user: str | None = None
    db_password: str | None = None
    db_sslmode: str = "prefer"

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

    @property
    def resolved_database_url(self) -> str:
        """DB_* parts win over DATABASE_URL when DB_HOST is set."""
        if not self.db_host:
            return self.database_url
        url = URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"sslmode": self.db_sslmode},
        )
        return url.render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
