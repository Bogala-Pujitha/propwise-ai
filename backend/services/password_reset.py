"""
Secure password-reset token helpers.

This module does not change the existing User schema. It uses Flask's
SECRET_KEY and time-limited signed tokens, so the database does not need a
new reset-token table just to implement the core reset mechanism.
"""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from flask import current_app


SALT = "propwise-password-reset-v1"


def _serializer():
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt=SALT,
    )


def generate_reset_token(user):
    """Create a short-lived signed token containing the user id and email."""
    return _serializer().dumps(
        {
            "user_id": int(user.id),
            "email": user.email,
        }
    )


def verify_reset_token(token, max_age=1800):
    """
    Return (user_id, email) for a valid token, otherwise None.

    `max_age` defaults to 30 minutes.
    """
    try:
        payload = _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None

    if not payload.get("user_id") or not payload.get("email"):
        return None

    return int(payload["user_id"]), payload["email"]
