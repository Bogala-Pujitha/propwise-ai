"""
Central activity/event tracking for PropWise AI.

Uses the existing Activity model from app.models.database when available,
or the legacy model exported from app.__init__ in the current application.
"""
import json
from datetime import datetime

from flask_login import current_user


def _models():
    try:
        from app.models.database import Activity, db
        return db, Activity
    except (ImportError, AttributeError):
        from app import db, Activity
        return db, Activity


def record_activity(activity_type, details=None, user_id=None, commit=True):
    """Persist a normalized activity record."""
    db, Activity = _models()

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

    activity = Activity(
        user_id=resolved_user_id,
        activity_type=str(activity_type)[:50],
        details=payload,
    )
    db.session.add(activity)

    if commit:
        db.session.commit()

    return activity


def track_event(event_name, payload=None):
    """Convenience wrapper for application/controllers."""
    return record_activity(event_name, payload)


def track_request_event(event_name, payload=None):
    """
    Safe event tracker for views/controllers.

    Tracking errors should not break the primary user action.
    """
    try:
        return record_activity(event_name, payload)
    except Exception:
        db, _ = _models()
        db.session.rollback()
        return None
