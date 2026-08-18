"""Application configuration and stable project paths."""

import os
from datetime import timedelta
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_DIR.parent


def default_config() -> dict:
    """Build configuration at application-creation time, not import time."""
    if os.environ.get("PROPWISE_TESTING") == "1":
        database_uri = "sqlite:///:memory:"
    else:
        configured_url = os.environ.get("DATABASE_URL")
        if configured_url:
            # Keep the existing production contract: an explicit DATABASE_URL
            # must be a PostgreSQL URL, while local development keeps SQLite.
            from app.config.database import get_database_url

            database_uri = get_database_url()
        else:
            database_uri = f"sqlite:///{APP_DIR / 'propwise.db'}"

    config = {
        "SECRET_KEY": os.environ.get(
            "SECRET_KEY", "propwise-ai-secret-key-2024"
        ),
        "SQLALCHEMY_DATABASE_URI": database_uri,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
        "PERMANENT_SESSION_LIFETIME": timedelta(minutes=30),
        "DATA_DIR": str(PROJECT_ROOT / "data"),
        "RAW_DIR": str(PROJECT_ROOT / "data" / "raw"),
        "PROCESSED_DIR": str(PROJECT_ROOT / "data" / "processed"),
        "MODELS_DIR": str(PROJECT_ROOT / "models"),
        "REPORTS_DIR": str(PROJECT_ROOT / "reports"),
    }

    if database_uri.startswith("postgresql+"):
        config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

    return config


class Config:
    """Compatibility configuration object for deployment tooling."""

    BASE_DIR = str(APP_DIR)
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "propwise-ai-secret-key-2024"
    )
    SQLALCHEMY_DATABASE_URI = default_config()["SQLALCHEMY_DATABASE_URI"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATA_DIR = str(PROJECT_ROOT / "data")
    RAW_DIR = str(PROJECT_ROOT / "data" / "raw")
    PROCESSED_DIR = str(PROJECT_ROOT / "data" / "processed")
    MODELS_DIR = str(PROJECT_ROOT / "models")
    REPORTS_DIR = str(PROJECT_ROOT / "reports")
