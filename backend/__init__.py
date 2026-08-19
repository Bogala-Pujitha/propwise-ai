"""Public application package and backward-compatible runtime exports."""

from __future__ import annotations

from backend.config.config import APP_DIR
from backend.extensions import bcrypt, db, load_user, login_manager
from backend.factory import create_app
from backend.models import Activity, Admin, AuditLog, Comparable, Prediction, User
from backend.runtime import get_runtime
from backend.security import admin_required
from backend.services.activity_service import record_activity


# Existing scripts and tests import ``app`` directly.  Keep that interface
# while the implementation now comes from the application factory.
app = create_app()
BASE_DIR = str(APP_DIR)

# Legacy read-only exports are synchronized whenever ``init_engine`` is called.
VALUATION_ENGINE = None
MASTER_DF = None
DROPDOWN_DATA = None


def _sync_runtime_exports(application=None):
    runtime = get_runtime(application or app)
    globals()["VALUATION_ENGINE"] = runtime.valuation_engine
    globals()["MASTER_DF"] = runtime.master_df
    globals()["DROPDOWN_DATA"] = runtime.dropdown_data
    return runtime


def init_engine():
    """Load ML resources lazily and retain the previous public helper."""
    runtime = get_runtime(app).initialize()
    _sync_runtime_exports(app)
    return runtime.valuation_engine


def initialize_database(application=None):
    """Create the unchanged schema in the configured database when requested."""
    application = application or app
    with application.app_context():
        db.create_all()


def log_activity(user_id, activity_type, details):
    """Compatibility wrapper for legacy callers that commit with their request."""
    return record_activity(
        user_id=user_id,
        activity_type=activity_type,
        details=details,
        commit=False,
    )


def ensure_default_admin(application=None):
    """Create the documented development admin only when it does not exist."""
    application = application or app
    with application.app_context():
        if User.query.filter_by(username="admin").first():
            return False
        admin = User(
            username="admin",
            email="admin@propwise.ai",
            password_hash=bcrypt.generate_password_hash("admin123").decode("utf-8"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        return True


__all__ = [
    "app",
    "create_app",
    "db",
    "bcrypt",
    "login_manager",
    "load_user",
    "User",
    "Admin",
    "Prediction",
    "Activity",
    "AuditLog",
    "Comparable",
    "BASE_DIR",
    "VALUATION_ENGINE",
    "MASTER_DF",
    "DROPDOWN_DATA",
    "admin_required",
    "initialize_database",
    "init_engine",
    "log_activity",
    "ensure_default_admin",
]
