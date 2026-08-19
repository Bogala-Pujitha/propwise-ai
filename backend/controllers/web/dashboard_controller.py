"""Dashboard browser controller."""

from flask import jsonify, render_template
from flask_login import current_user, login_required

from backend.runtime import get_runtime
from backend.services.dashboard_service import (
    admin_dashboard_context,
)


@login_required
def api_dropdown_data():

    runtime = get_runtime()

    if runtime.dropdown_data is None:

        from backend.services.geocoding import (
            get_all_dropdown_data
        )

        runtime.dropdown_data = (
            get_all_dropdown_data(
                runtime.master_df
            )
        )

    return jsonify(
        runtime.dropdown_data
    )


@login_required
def dashboard():
    """Render shared dashboard for authenticated users."""

    runtime = get_runtime()

    if runtime.dropdown_data is None:
        runtime.initialize()

    context = admin_dashboard_context(
        runtime.dropdown_data
    )

    context["current_user"] = current_user

    return render_template(
        "admin_dashboard.html",
        **context,
    )


@login_required
def user_dashboard():
    """Explicit user dashboard route."""

    return dashboard()