"""Authentication helpers built on the repository's existing Flask-Login/Bcrypt stack."""
from typing import Optional, Tuple

from flask_login import login_user, logout_user


def register_user(User, db, bcrypt, *, username: str, email: str, password: str):
    username = (username or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not username or not email or not password:
        raise ValueError("Username, email and password are required.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    if User.query.filter_by(username=username).first():
        raise ValueError("Username already exists.")
    if User.query.filter_by(email=email).first():
        raise ValueError("Email already registered.")

    user = User(
        username=username,
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        role="user",
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(User, bcrypt, *, username: str, password: str, role: str = "user"):
    username = (username or "").strip()
    password = password or ""
    role = (role or "user").lower()

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return None
    if role == "admin" and getattr(user, "role", "user") != "admin":
        return None

    login_user(user)
    return user


def logout_account():
    logout_user()


def is_admin(user) -> bool:
    return bool(getattr(user, "is_authenticated", False) and getattr(user, "role", "user") == "admin")
