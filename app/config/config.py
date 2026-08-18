"""Application configuration and stable project paths."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_DIR.parent


def default_config() -> dict:
    """Build configuration at application-creation time."""
    if os.environ.get("PROPWISE_TESTING") == "1":
        # Keep lightweight SQLite for isolated unit/integration tests.
        database_uri = "sqlite:///:memory:"
        engine_options = {}
    else:
        from app.config.database import get_database_url

        database_uri = get_database_url()
        engine_options = {
            "pool_pre_ping": True,
            "pool_recycle": 280,
        }

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        # CI/testing supplies its own secret. Production must supply one.
        if os.environ.get("FLASK_ENV") != "testing":
            raise RuntimeError(
                "SECRET_KEY is required outside testing."
            )
        secret_key = "ci-testing-secret"

    return {
        "SECRET_KEY": secret_key,
        "SQLALCHEMY_DATABASE_URI": database_uri,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": engine_options,
        "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
        "PERMANENT_SESSION_LIFETIME": timedelta(minutes=30),
        "DATA_DIR": str(PROJECT_ROOT / "data"),
        "RAW_DIR": str(PROJECT_ROOT / "data" / "raw"),
        "PROCESSED_DIR": str(PROJECT_ROOT / "data" / "processed"),
        "MODELS_DIR": str(PROJECT_ROOT / "models"),
        "REPORTS_DIR": str(PROJECT_ROOT / "reports"),
    }


class Config:
    """Compatibility configuration object for deployment tooling."""

    BASE_DIR = str(APP_DIR)

    _secret_key = os.environ.get("SECRET_KEY")
    SECRET_KEY = _secret_key or "ci-testing-secret"

    SQLALCHEMY_DATABASE_URI = default_config()["SQLALCHEMY_DATABASE_URI"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = default_config()["SQLALCHEMY_ENGINE_OPTIONS"]

    DATA_DIR = str(PROJECT_ROOT / "data")
    RAW_DIR = str(PROJECT_ROOT / "data" / "raw")
    PROCESSED_DIR = str(PROJECT_ROOT / "data" / "processed")
    MODELS_DIR = str(PROJECT_ROOT / "models")
    REPORTS_DIR = str(PROJECT_ROOT / "reports")
