from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from backend.extensions import db
from backend.models import Activity, Prediction, User
from backend.services.auth_service import is_admin
from backend.services.analytics import build_admin_summary

analytics_bp = Blueprint("analytics_api", __name__, url_prefix="/api/analytics")


@analytics_bp.get("/admin/summary")
@login_required
def admin_summary():
    if not is_admin(current_user):
        return jsonify({"success": False, "error": "Admin access required"}), 403
    summary = build_admin_summary(db, User, Prediction, Activity)
    return jsonify({
        "total_users": summary["total_users"],
        "total_predictions": summary["total_predictions"],
        "total_activities": summary["total_activities"],
        "average_prediction": summary["average_prediction"],
        "predictions_by_type": summary["predictions_by_type"],
        "predictions_by_city": summary["predictions_by_city"],
        "predictions_by_locality": summary["predictions_by_locality"],
        "predictions_by_reliability": summary["predictions_by_reliability"],
    })
