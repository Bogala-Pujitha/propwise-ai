"""Administrator HTML controller."""

from flask import render_template
from flask_login import login_required

from backend.runtime import get_runtime
from backend.security import admin_required
from backend.services.dashboard_service import (
    admin_analytics_context,
    admin_dashboard_context,
    admin_users_context,
    recent_audit_logs,
)


@login_required
@admin_required
def admin_dashboard():
    runtime = get_runtime()
    if runtime.dropdown_data is None:
        runtime.initialize()
    return render_template(
        "admin_dashboard.html",
        **admin_dashboard_context(runtime.dropdown_data),
    )


@login_required
@admin_required
def admin_users():
    return render_template("admin_users.html", **admin_users_context())


@login_required
@admin_required
def admin_analytics():
    return render_template("admin_analytics.html", **admin_analytics_context())


@login_required
@admin_required
def admin_audit():
    return render_template("admin_audit.html", logs=recent_audit_logs())
