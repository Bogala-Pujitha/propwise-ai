"""Security defaults for the Python/venv Flask deployment."""
import os
from datetime import timedelta


class SecurityConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
