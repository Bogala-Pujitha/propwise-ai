import os
from datetime import timedelta
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_DIR.parent


def default_config() -> dict:
    if os.environ.get("PROPWISE_TESTING") == "1":
        database_uri = "sqlite:///:memory:"
        engine_options = {}
    else:
        configured_url = os.environ.get("DATABASE_URL")
        if configured_url:
            from backend.config.database import get_database_url
            database_uri = get_database_url()
            engine_options = {
                "pool_pre_ping": True,
                "pool_recycle": 280,
            }
        else:
            database_uri = f"sqlite:///{APP_DIR / 'propwise.db'}"
            engine_options = {}

    secret_key = os.environ.get("SECRET_KEY", "propwise-ai-secret-key-2024")

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