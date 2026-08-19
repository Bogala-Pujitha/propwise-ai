from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from backend.extensions import db
from backend.models import Activity, Prediction, User
from backend.services.analytics import build_user_summary
from backend.services.activity_service import record_activity

user_bp = Blueprint("user_api", __name__, url_prefix="/api/user")


@user_bp.get("/profile")
@login_required
def profile():
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    })


@user_bp.get("/history")
@login_required
def history():
    summary = build_user_summary(User, Prediction, Activity, current_user.id)
    return jsonify({
        "prediction_count": summary["prediction_count"],
        "activity_count": summary["activity_count"],
        "predictions": [
            {
                "id": p.id,
                "property_type": p.property_type,
                "city": p.city,
                "locality": p.locality,
                "predicted_price": p.predicted_price,
                "reliability": p.reliability,
                "recommendation": p.recommendation,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in summary["recent_predictions"]
        ],
        "activities": [
            {
                "type": a.activity_type,
                "details": a.details,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in summary["recent_activities"]
        ],
    })


@user_bp.post("/track")
@login_required
def track():
    record_activity(db, Activity, current_user.id, "ui_event", "User dashboard event")
    db.session.commit()
    return jsonify({"success": True})
