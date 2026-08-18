"""MySQL database configuration for PropWise AI."""

from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit


def get_database_url() -> str:
    """Return a normalized SQLAlchemy MySQL URL.

    Accepted input forms:
      mysql://user:password@host:3306/database
      mysql+pymysql://user:password@host:3306/database

    The normalized output always uses mysql+pymysql.
    """
    url = os.environ.get("DATABASE_URL", "").strip()

    if not url:
        raise RuntimeError(
            "DATABASE_URL is required. Configure MySQL before starting "
            "PropWise AI."
        )

    if url.startswith("mysql://"):
        url = "mysql+pymysql://" + url[len("mysql://") :]

    if not url.startswith("mysql+pymysql://"):
        raise RuntimeError(
            "DATABASE_URL must use MySQL with PyMySQL "
            "(mysql:// or mysql+pymysql://)."
        )

    # Ensure utf8mb4 is requested without destroying an existing query string.
    parts = urlsplit(url)
    query = parts.query

    if "charset=" not in query.lower():
        query = f"{query}&charset=utf8mb4" if query else "charset=utf8mb4"

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            query,
            parts.fragment,
        )
    )


def configure_database(app) -> None:
    """Apply MySQL settings to a Flask application."""
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
