"""Password-reset API backed by the existing signed-token helper."""

from __future__ import annotations

import os

from flask import Blueprint, jsonify, request, url_for
from werkzeug.security import generate_password_hash

from app.extensions import bcrypt, db
from app.models import User
from app.services.email_service import send_password_reset_email
from app.services.password_reset import generate_reset_token, verify_reset_token

password_reset_bp = Blueprint(
    "password_reset_api",
    __name__,
    url_prefix="/api/auth",
)


@password_reset_bp.post("/forgot-password")
def forgot_password():
    data = request.get_json(silent=True) or request.form
    email = str(data.get("email", "")).strip().lower()

    # Do not reveal whether the account exists.
    response = {
        "success": True,
        "message": "If the account exists, a reset email will be sent.",
    }

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify(response)

    token = generate_reset_token(user)
    base_url = os.getenv("RESET_BASE_URL", "").rstrip("/")
    if base_url:
        reset_url = f"{base_url}/reset-password?token={token}"
    else:
        reset_url = url_for(
            "password_reset_api.reset_password",
            token=token,
            _external=True,
        )

    try:
        sent = send_password_reset_email(
            recipient=user.email,
            reset_url=reset_url,
        )
    except Exception:
        sent = False

    # Development-only aid: allow the caller to know delivery is not configured
    # without exposing reset tokens. Configure SMTP for real deployments.
    if not sent and os.getenv("FLASK_ENV") != "production":
        response["delivery_configured"] = False

    return jsonify(response)


@password_reset_bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or request.form
    token = str(data.get("token", "")).strip()
    password = str(data.get("password", ""))

    payload = verify_reset_token(token)
    if not payload:
        return jsonify(
            {"success": False, "error": "Invalid or expired reset token"}
        ), 400

    user_id, email = payload
    user = User.query.get(user_id)

    if not user or user.email.lower() != email.lower():
        return jsonify({"success": False, "error": "Invalid reset token"}), 400

    if len(password) < 8:
        return jsonify(
            {"success": False, "error": "Password must be at least 8 characters"}
        ), 400

    # The project's canonical authentication stack uses bcrypt. Import it here
    # so the password remains compatible with existing login().
    try:
        user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    except Exception:
        user.password_hash = generate_password_hash(password)

    db.session.commit()
    return jsonify({"success": True, "message": "Password reset successfully"})
