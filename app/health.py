"""Health and readiness endpoint helpers."""

from __future__ import annotations

from flask import Blueprint, jsonify


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@health_bp.get("/ready")
def ready():
    # Keep readiness lightweight. Database connectivity should be checked
    # separately in deployment/startup validation if the platform requires it.
    return jsonify({"status": "ready"}), 200
