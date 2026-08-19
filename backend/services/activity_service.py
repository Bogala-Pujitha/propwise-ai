"""Central activity and audit persistence for PropWise AI."""
import json

from flask_login import current_user

from backend.extensions import db as extension_db
from backend.models import Activity, AuditLog


def _models():
    return extension_db, Activity


def record_activity(
    db=None,
    model_class=None,
    user_id=None,
    activity_type=None,
    details=None,
    commit=True,
):
    """Persist a normalized activity record."""
    default_db, default_model = _models()
    db = db or default_db
    model_class = model_class or default_model
    resolved_user_id = user_id
    if resolved_user_id is None and current_user.is_authenticated:
        resolved_user_id = current_user.id

    if resolved_user_id is None:
        return None

    if isinstance(details, (dict, list)):
        payload = json.dumps(details, default=str)
    elif details is None:
        payload = ""
    else:
        payload = str(details)

    activity = model_class(
        user_id=resolved_user_id,
        activity_type=str(activity_type or "")[:50],
        details=payload,
    )
    db.session.add(activity)

    if commit:
        db.session.commit()

    return activity


def record_audit(
    db=None,
    model_class=None,
    admin_id=None,
    action=None,
    details=None,
    commit=True,
):
    """Persist an audit log entry for an admin action."""
    db = db or extension_db
    model_class = model_class or AuditLog
    if isinstance(details, (dict, list)):
        payload = json.dumps(details, default=str)
    elif details is None:
        payload = ""
    else:
        payload = str(details)

    entry = model_class(
        admin_id=admin_id,
        action=str(action or "")[:100],
        details=payload,
    )
    db.session.add(entry)
    if commit:
        db.session.commit()
    return entry


def track_event(event_name, payload=None):
    """Convenience wrapper for application/controllers."""
    db, Activity = _models()
    return record_activity(db, Activity, None, event_name, payload)


def track_request_event(event_name, payload=None):
    """
    Safe event tracker for views/controllers.

    Tracking errors should not break the primary user action.
    """
    try:
        return track_event(event_name, payload)
    except Exception:
        db, _ = _models()
        db.session.rollback()
        return None
