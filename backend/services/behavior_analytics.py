"""Behavioral analytics derived from the existing Activity table.

The service parses structured JSON event details in Python so it remains
portable across SQLite and PostgreSQL.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from backend.extensions import db
from backend.models import Activity, User


PROPERTY_EVENTS = {"property_view", "comparable_search", "similar_property_search"}
LOCATION_EVENTS = {"location_view", "property_view", "comparable_search"}
SEARCH_EVENTS = {"comparable_search", "similar_property_search", "what_if_run"}


def _deps():
    return db, Activity, User


def _parse_details(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {}


def _events(days: int = 30):
    db, Activity, User = _deps()
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        Activity.query
        .filter(Activity.created_at >= since)
        .order_by(Activity.created_at.desc())
        .all()
    )
    return db, Activity, User, rows


def _rank(counter: Counter, limit: int = 10):
    return [
        {"key": key, "count": count}
        for key, count in counter.most_common(limit)
    ]


def build_behavior_dashboard(days: int = 30, limit: int = 10):
    """Return property, location, search and activity analytics."""
    _db, _Activity, User, rows = _events(days)

    property_views = Counter()
    locations = Counter()
    comparable_targets = Counter()
    similar_targets = Counter()
    activities = Counter()
    active_users = Counter()

    for event in rows:
        event_type = event.activity_type or "unknown"
        activities[event_type] += 1
        if event.user_id is not None:
            active_users[event.user_id] += 1

        payload = _parse_details(event.details)
        property_id = payload.get("property_id")
        locality = payload.get("locality")
        city = payload.get("city")

        if event_type == "property_view":
            if property_id is not None:
                property_views[str(property_id)] += 1

        if event_type in LOCATION_EVENTS:
            location_key = " / ".join(
                str(x) for x in (locality, city) if x
            )
            if location_key:
                locations[location_key] += 1

        if event_type == "comparable_search":
            target = payload.get("property_id") or payload.get("locality")
            if target is not None:
                comparable_targets[str(target)] += 1

        if event_type == "similar_property_search":
            target = payload.get("property_id") or payload.get("locality")
            if target is not None:
                similar_targets[str(target)] += 1

    active_user_rows = []
    for user_id, count in active_users.most_common(limit):
        user = User.query.get(user_id)
        if user:
            active_user_rows.append(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "activity_count": count,
                }
            )

    return {
        "period_days": days,
        "most_active_users": active_user_rows,
        "most_viewed_properties": _rank(property_views, limit),
        "popular_locations": _rank(locations, limit),
        "frequently_compared": _rank(comparable_targets, limit),
        "similar_property_searches": _rank(similar_targets, limit),
        "activity_types": _rank(activities, limit),
    }
