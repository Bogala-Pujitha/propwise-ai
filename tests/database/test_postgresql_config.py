import pytest


def test_database_url_requires_postgresql(monkeypatch):
    from app.config.database import get_database_url
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        get_database_url()


def test_database_url_accepts_postgresql(monkeypatch):
    from app.config.database import get_database_url
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg2://propwise:secret@localhost:5432/propwise",
    )
    assert get_database_url().startswith("postgresql+psycopg2://")


def test_database_url_rejects_sqlite(monkeypatch):
    from app.config.database import get_database_url
    monkeypatch.setenv("DATABASE_URL", "sqlite:///propwise.db")
    with pytest.raises(RuntimeError):
        get_database_url()
