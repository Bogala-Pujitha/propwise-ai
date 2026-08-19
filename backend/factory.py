"""Application factory for the PropWise AI web application."""

from __future__ import annotations

from flask import Flask

from backend.config.config import APP_DIR, PROJECT_ROOT, default_config
from backend.extensions import bcrypt, cors, db, login_manager
from backend.runtime import PropWiseRuntime


def create_app(config_overrides: dict | None = None) -> Flask:
    """Create a configured Flask application without creating database data."""
    application = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "frontend" / "templates"),
        static_folder=str(PROJECT_ROOT / "frontend" / "static"),
    )
    application.config.from_mapping(default_config())
    if config_overrides:
        application.config.from_mapping(config_overrides)

    # Import ORM models before extension setup so SQLAlchemy has the complete
    # unchanged schema when an operator later runs ``db.create_all()``.
    import backend.models  # noqa: F401

    db.init_app(application)
    bcrypt.init_app(application)
    cors.init_app(application)
    login_manager.init_app(application)
    login_manager.login_view = "login"

    application.extensions["propwise_runtime"] = PropWiseRuntime(PROJECT_ROOT)

    from backend.controllers import register_blueprints
    from backend.controllers.web import register_web_routes

    register_blueprints(application)
    register_web_routes(application)
    return application
