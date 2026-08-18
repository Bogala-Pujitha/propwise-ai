"""Dashboard browser controller."""

from flask import jsonify, render_template
from flask_login import current_user, login_required

from app.runtime import get_runtime
from app.services.dashboard_service import user_dashboard_context


@login_required
def api_dropdown_data():
    runtime = get_runtime()
    if runtime.dropdown_data is None:
        from app.services.geocoding import get_all_dropdown_data

        runtime.dropdown_data = get_all_dropdown_data(runtime.master_df)
    return jsonify(runtime.dropdown_data)


@login_required
def dashboard():
    runtime = get_runtime()
    if runtime.dropdown_data is None:
        runtime.initialize()
    return render_template(
        "dashboard.html",
        **user_dashboard_context(current_user.id, runtime.dropdown_data),
    )
