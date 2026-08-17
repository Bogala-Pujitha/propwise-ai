"""Persistent user/admin activity and audit helpers."""
from datetime import datetime


def record_activity(db, Activity, user_id: int, activity_type: str, details: str = ""):
    activity = Activity(
        user_id=user_id,
        activity_type=activity_type,
        details=details,
        created_at=datetime.utcnow(),
    )
    db.session.add(activity)
    return activity


def record_audit(db, AuditLog, admin_id: int, action: str, details: str = ""):
    log = AuditLog(
        admin_id=admin_id,
        action=action,
        details=details,
        created_at=datetime.utcnow(),
    )
    db.session.add(log)
    return log
