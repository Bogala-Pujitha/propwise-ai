from datetime import datetime
from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required

from backend.extensions import bcrypt, db
from backend.models import Activity, User
from backend.services.auth_service import register_user, authenticate_user, logout_account, is_admin
from backend.services.activity_service import record_activity


auth_bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def api_register():
    data = request.get_json(silent=True) or request.form
    try:
        user = register_user(
            User, db, bcrypt,
            username=data.get("username", ""),
            email=data.get("email", ""),
            password=data.get("password", ""),
        )
        record_activity(db, Activity, user.id, "register", "Account created")
        db.session.commit()
        return jsonify({"success": True, "user_id": user.id, "role": user.role}), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400


@auth_bp.post("/login")
def api_login():
    data = request.get_json(silent=True) or request.form
    user = authenticate_user(
        User, bcrypt,
        username=data.get("username", ""),
        password=data.get("password", ""),
        role=data.get("role", "user"),
    )
    if not user:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    session.permanent = True
    session["login_time"] = datetime.utcnow().isoformat()
    record_activity(db, Activity, user.id, "login", "API login")
    db.session.commit()
    return jsonify({"success": True, "user_id": user.id, "username": user.username, "role": user.role})


@auth_bp.post("/logout")
@login_required
def api_logout():
    record_activity(db, Activity, current_user.id, "logout", "API logout")
    db.session.commit()
    logout_account()
    return jsonify({"success": True})


@auth_bp.get("/me")
@login_required
def api_me():
    return jsonify({
        "authenticated": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_admin": is_admin(current_user),
    })
