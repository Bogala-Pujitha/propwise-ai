from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit


def get_database_url() -> str:
    if os.environ.get("PROPWISE_TESTING") == "1":
        return "sqlite:///:memory:"

    raw = os.environ.get("DATABASE_URL", "").strip()
    if not raw:
        raise RuntimeError("DATABASE_URL is required outside testing.")

    if raw.startswith("mysql://"):
        raw = "mysql+pymysql://" + raw[len("mysql://"):]

    if not raw.startswith("mysql+pymysql://"):
        raise RuntimeError("DATABASE_URL must be a MySQL/PyMySQL URL.")

    parts = urlsplit(raw)
    query = parts.query
    if "charset=" not in query.lower():
        query = f"{query}&charset=utf8mb4" if query else "charset=utf8mb4"

    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def configure_database(app) -> None:
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_url()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
