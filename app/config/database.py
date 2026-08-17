"""Native PostgreSQL configuration for PropWise AI."""

import os


def get_database_url() -> str:
    """Return the PostgreSQL connection URL used by the application."""
    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError(
            "DATABASE_URL is required. "
            "Set it to a PostgreSQL connection URL before starting PropWise AI."
        )

    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]

    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]

    if not url.startswith("postgresql+psycopg2://"):
        raise RuntimeError(
            "DATABASE_URL must use PostgreSQL, for example: "
            "postgresql+psycopg2://user:password@localhost:5432/propwise"
        )

    return url


def configure_database(app) -> None:
    """Configure the existing Flask-SQLAlchemy instance for PostgreSQL."""
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Production-friendly connection checks.
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
    }
