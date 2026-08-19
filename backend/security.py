"""Production security and authorization helpers for the Flask application."""

from __future__ import annotations

from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(view_func):
    """Protect browser routes while preserving the legacy login redirect UX."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if (
            not current_user.is_authenticated
            or getattr(current_user, "role", None) != "admin"
        ):
            flash("Admin access required", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


def configure_security(app):
    """Apply safe HTTP security headers.

    HSTS is deliberately enabled only when HTTPS is explicitly configured.
    This avoids breaking local HTTP development.
    """

    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("REMEMBER_COOKIE_HTTPONLY", True)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(self)",
        )

        if app.config.get("FORCE_HTTPS"):
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response

    return app
