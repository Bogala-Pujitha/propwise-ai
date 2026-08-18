"""Dashboard browser controller.

Normal users reuse the exact same dashboard/admin templates so the
user-side interface matches the admin interface.

Important:
- Existing admin_controller.py is NOT modified.
- Existing admin templates are NOT modified.
- Admin routes remain protected by admin_required.
- User routes render the same templates with user-safe navigation links.
"""

from flask import jsonify, render_template
from flask_login import current_user, login_required

from app.runtime import get_runtime
from app.services.dashboard_service import (
    admin_analytics_context,
    admin_dashboard_context,
    admin_users_context,
    recent_audit_logs,
)


def _render_user_admin_template(template_name, **context):
    """Render an existing admin template for a normal authenticated user.

    The HTML/CSS/template itself is unchanged.
    Only navigation URLs are rewritten in this user-side response so
    clicking Users / Analytics / Audit / Overview does not send the
    normal user into admin-only endpoints.
    """
    html = render_template(template_name, **context)

    # Replace longer paths first so '/admin' does not accidentally
    # modify '/admin/users', '/admin/analytics', etc.
    navigation_replacements = (
        ("/admin/users", "/user/users"),
        ("/admin/analytics", "/user/analytics"),
        ("/admin/audit", "/user/audit"),
        ("/admin", "/dashboard"),
    )

    for old_path, new_path in navigation_replacements:
        html = html.replace(old_path, new_path)

    return html


@login_required
def api_dropdown_data():
    """Return dropdown data for authenticated users."""
    runtime = get_runtime()

    if runtime.dropdown_data is None:
        from app.services.geocoding import get_all_dropdown_data

        runtime.dropdown_data = get_all_dropdown_data(runtime.master_df)

    return jsonify(runtime.dropdown_data)


@login_required
def dashboard():
    """Normal-user dashboard rendered with the exact admin dashboard UI."""
    runtime = get_runtime()

    if runtime.dropdown_data is None:
        runtime.initialize()

    return _render_user_admin_template(
        "admin_dashboard.html",
        **admin_dashboard_context(runtime.dropdown_data),
    )


@login_required
def user_dashboard():
    """Explicit user dashboard route.

    This points to the same interface as /dashboard.
    """
    runtime = get_runtime()

    if runtime.dropdown_data is None:
        runtime.initialize()

    return _render_user_admin_template(
        "admin_dashboard.html",
        **admin_dashboard_context(runtime.dropdown_data),
    )


@login_required
def user_users():
    """Users page available to authenticated normal users."""
    return _render_user_admin_template(
        "admin_users.html",
        **admin_users_context(),
    )


@login_required
def user_analytics():
    """Analytics page available to authenticated normal users."""
    return _render_user_admin_template(
        "admin_analytics.html",
        **admin_analytics_context(),
    )


@login_required
def user_audit():
    """Audit page available to authenticated normal users."""
    return _render_user_admin_template(
        "admin_audit.html",
        logs=recent_audit_logs(),
    )