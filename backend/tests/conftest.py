import os
import tempfile
from pathlib import Path

import pytest

# Point the app at a throwaway SQLite file before it is imported.
_tmpdir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmpdir) / 'test.db'}"
os.environ["SOLVER_TIME_LIMIT_S"] = "1"
os.environ["SEED_ON_STARTUP"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


@pytest.fixture()
def db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        yield session


@pytest.fixture()
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def seeded_client(db):
    seed(db)
    with TestClient(app) as c:
        yield c
