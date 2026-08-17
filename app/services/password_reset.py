"""Password-reset token helpers.

This module generates signed reset tokens. Email delivery is intentionally kept
outside the core app so an SMTP/provider can be added later without changing auth logic.
"""
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


def make_reset_token(secret_key: str, user_id: int) -> str:
    serializer = URLSafeTimedSerializer(secret_key, salt="propwise-password-reset")
    return serializer.dumps({"user_id": int(user_id)})


def read_reset_token(secret_key: str, token: str, max_age_seconds: int = 1800):
    serializer = URLSafeTimedSerializer(secret_key, salt="propwise-password-reset")
    try:
        payload = serializer.loads(token, max_age=max_age_seconds)
        return int(payload["user_id"])
    except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
        return None
