"""Structured behavioral event tracking for PropWise AI.

This reuses the repository's existing Activity model rather than introducing
another database table. Event-specific fields are stored as JSON in Activity.details.
"""

from __future__ import annotations

import json
from typing import Any

from flask_login import current_user

from backend.extensions import db
from backend.models import Activity


def _deps():
    return db, Activity


def track(
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    user_id: int | None = None,
    commit: bool = True,
):
    """Record a structured event without breaking the primary user action."""
    db, Activity = _deps()

    resolved_user_id = user_id
    if resolved_user_id is None and current_user.is_authenticated:
        resolved_user_id = current_user.id

    if resolved_user_id is None:
        return None

    details = payload or {}
    record = Activity(
        user_id=resolved_user_id,
        activity_type=event_type[:50],
        details=json.dumps(details, default=str),
    )
    db.session.add(record)

    if commit:
        db.session.commit()

    return record


def safe_track(
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    user_id: int | None = None,
):
    """Best-effort tracking; analytics failure must not break the main request."""
    db, _ = _deps()
    try:
        return track(event_type, payload, user_id=user_id, commit=True)
    except Exception:
        db.session.rollback()
        return None
