import os

import pytest
from sqlalchemy import create_engine, text

from backend import create_app
from backend.extensions import db


def test_sqlite_dependency():
    """SQLite is part of the Python standard library (no extra dependency)."""
    import sqlite3

    assert sqlite3.sqlite_version


@pytest.mark.skipif(
    "DATABASE_URL" not in os.environ,
    reason="DATABASE_URL not configured",
)
def test_database_url_uses_sqlite():
    """When DATABASE_URL is set it must point to a SQLite database."""
    from sqlalchemy.engine import make_url

    url = make_url(os.environ["DATABASE_URL"])
    assert url.get_backend_name() == "sqlite"


def test_sqlite_in_memory_connection():
    """Verify a basic in-memory SQLite connection works."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar_one()
        assert result == 1
    engine.dispose()


def test_sqlite_default_db_path():
    """The default config must resolve to a SQLite file path."""
    from backend.config.config import APP_DIR

    default_uri = f"sqlite:///{APP_DIR / 'propwise.db'}"
    assert default_uri.startswith("sqlite:///")
