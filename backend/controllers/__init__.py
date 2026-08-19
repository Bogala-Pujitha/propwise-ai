"""Blueprint registration for the modular application layer.

These APIs are additive. Existing HTML routes in app/__init__.py can remain
in place until the application is fully migrated to controllers.
"""

from .auth_controller import auth_bp
from .user_controller import user_bp
from .admin_controller import admin_bp
from .analytics_controller import analytics_bp
from .valuation_controller import valuation_bp
from .comparable_controller import comparable_bp
from .what_if_controller import what_if_bp
from .behavior_controller import behavior_bp
from .map_controller import map_bp
from .password_reset_controller import password_reset_bp


def register_blueprints(app):
    """Register every API controller once for this application instance."""
    blueprints = (
        auth_bp,
        user_bp,
        admin_bp,
        analytics_bp,
        valuation_bp,
        comparable_bp,
        what_if_bp,
        behavior_bp,
        map_bp,
        password_reset_bp,
    )
    for blueprint in blueprints:
        if blueprint.name not in app.blueprints:
            app.register_blueprint(blueprint)
