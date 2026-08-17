"""Blueprint registration for the modular application layer.

These APIs are additive. Existing HTML routes in app/__init__.py can remain in place
until the application is fully migrated to controllers.
"""
from .auth_controller import auth_bp
from .user_controller import user_bp
from .admin_controller import admin_bp
from .analytics_controller import analytics_bp
from .valuation_controller import valuation_bp
from .comparable_controller import comparable_bp
from .what_if_controller import what_if_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(valuation_bp)
    app.register_blueprint(comparable_bp)
    app.register_blueprint(what_if_bp)
