"""Authenticated behavior-event endpoints.

These endpoints are intentionally small; normal application routes should call
behavior_tracking.track() directly when the event happens.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import login_required

from backend.services.behavior_tracking import safe_track

behavior_bp = Blueprint(
    "behavior_api",
    __name__,
    url_prefix="/api/behavior",
)


@behavior_bp.post("/track")
@login_required
def track_event():
    data = request.get_json(silent=True) or {}
    event_type = str(data.get("event_type", "")).strip()

    allowed = {
        "property_view",
        "location_view",
        "comparable_search",
        "similar_property_search",
        "what_if_run",
        "shap_view",
        "prediction_created",
        "bulk_valuation",
        "dashboard_view",
    }

    if event_type not in allowed:
        return jsonify({"success": False, "error": "Unsupported event type"}), 400

    payload = data.get("payload")
    if payload is not None and not isinstance(payload, dict):
        return jsonify({"success": False, "error": "payload must be an object"}), 400

    safe_track(event_type, payload or {})
    return jsonify({"success": True})
