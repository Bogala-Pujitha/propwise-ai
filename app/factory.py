"""Application factory for the PropWise AI web application."""

from __future__ import annotations

from flask import Flask

from app.config.config import APP_DIR, PROJECT_ROOT, default_config
from app.extensions import bcrypt, cors, db, login_manager
from app.runtime import PropWiseRuntime


def create_app(config_overrides: dict | None = None) -> Flask:
    """Create a configured Flask application without creating database data."""
    application = Flask(
        __name__,
        template_folder=str(APP_DIR / "views"),
        static_folder=str(APP_DIR / "static"),
    )
    application.config.from_mapping(default_config())
    if config_overrides:
        application.config.from_mapping(config_overrides)

    # Import ORM models before extension setup so SQLAlchemy has the complete
    # unchanged schema when an operator later runs ``db.create_all()``.
    import app.models  # noqa: F401

    db.init_app(application)
    bcrypt.init_app(application)
    cors.init_app(application)
    login_manager.init_app(application)
    login_manager.login_view = "login"

    application.extensions["propwise_runtime"] = PropWiseRuntime(PROJECT_ROOT)

    from app.controllers import register_blueprints
    from app.controllers.web import register_web_routes

    register_blueprints(application)
    register_web_routes(application)
    return application
