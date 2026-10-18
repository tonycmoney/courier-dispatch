from sqlalchemy.engine import make_url

from app.config import Settings
from app.db import _normalize_url


def test_database_url_used_by_default():
    assert Settings(database_url="sqlite:///x.db").resolved_database_url == "sqlite:///x.db"


def test_db_parts_build_postgres_url_and_escape_password():
    s = Settings(
        db_host="db.internal",
        db_user="app_admin",
        db_password="p@ss:w/rd",
        db_name="dispatch",
        db_sslmode="require",
    )
    url = make_url(s.resolved_database_url)
    assert url.drivername == "postgresql+psycopg"
    assert url.host == "db.internal"
    assert url.password == "p@ss:w/rd"
    assert url.database == "dispatch"
    assert url.query["sslmode"] == "require"


def test_normalize_heroku_style_url():
    assert _normalize_url("postgres://u:p@h/db") == "postgresql://u:p@h/db"
