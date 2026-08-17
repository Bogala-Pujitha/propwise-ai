from flask import Blueprint, jsonify
from flask_login import current_user

from app.services.auth_service import is_admin
from app.services.activity_service import record_audit
from app.services.analytics import build_admin_summary

admin_bp = Blueprint("admin_api", __name__, url_prefix="/api/admin")


def _deps():
    from app import db, User, Prediction, Activity, AuditLog
    return db, User, Prediction, Activity, AuditLog


def _admin_only():
    return is_admin(current_user)


@admin_bp.before_request
def require_admin():
    if not current_user.is_authenticated or not _admin_only():
        return jsonify({"success": False, "error": "Admin access required"}), 403


@admin_bp.get("/users")
def users():
    db, User, Prediction, Activity, AuditLog = _deps()
    rows = []
    for user in User.query.order_by(User.created_at.desc()).all():
        rows.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "prediction_count": Prediction.query.filter_by(user_id=user.id).count(),
            "activity_count": Activity.query.filter_by(user_id=user.id).count(),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    record_audit(db, AuditLog, current_user.id, "view_users", "Viewed user analytics API")
    db.session.commit()
    return jsonify({"users": rows})


@admin_bp.get("/dashboard")
def dashboard():
    db, User, Prediction, Activity, AuditLog = _deps()
    summary = build_admin_summary(db, User, Prediction, Activity)
    record_audit(db, AuditLog, current_user.id, "view_dashboard", "Viewed admin dashboard API")
    db.session.commit()
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


@admin_bp.get("/audit")
def audit():
    db, User, Prediction, Activity, AuditLog = _deps()
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return jsonify({
        "logs": [
            {
                "id": x.id,
                "admin_id": x.admin_id,
                "action": x.action,
                "details": x.details,
                "created_at": x.created_at.isoformat() if x.created_at else None,
            }
            for x in logs
        ]
    })
